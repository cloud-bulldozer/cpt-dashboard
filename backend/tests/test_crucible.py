from collections import defaultdict
from datetime import datetime, timezone
import json

from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
import pytest

import app.config
from app.services.crucible_svc import (
    CommonParams,
    CrucibleService,
    Graph,
    GraphList,
    Parser,
)
from tests.fake_elastic import Request


class TestParser:

    def test_parse_normal(self):
        """Test successful parsing of three terms"""

        t = Parser("foo:bar=x")
        assert ("foo", ":") == t._next_token([":", "="])
        assert ("bar", "=") == t._next_token([":", "="])
        assert ("x", None) == t._next_token([":", "="], optional=True)

    def test_parse_missing(self):
        """Test exception when a delimiter is missing"""

        t = Parser("foo:bar=x")
        assert ("foo", ":") == t._next_token([":", "="])
        assert ("bar", "=") == t._next_token([":", "="])
        with pytest.raises(HTTPException) as e:
            t._next_token(delimiters=[":", "="])
        assert 400 == e.value.status_code
        assert "Missing delimiter from :,= after 'x'" == e.value.detail

    def test_parse_quoted(self):
        """Test acceptance of quoted terms"""

        t = Parser("'foo':\"bar\"='x'")
        assert ("foo", ":") == t._next_token([":", "="])
        assert ("bar", "=") == t._next_token([":", "="])
        assert ("x", None) == t._next_token([":", "="], optional=True)

    def test_parse_bad_quoted(self):
        """Test detection of badly paired quotes"""

        t = Parser("'foo':'bar\"='x'")
        assert ("foo", ":") == t._next_token([":", "="])
        with pytest.raises(HTTPException) as e:
            t._next_token([":", "="])
        assert 400 == e.value.status_code
        assert "Unterminated quote at '\\'foo\\':\\'bar[\"]=\\'x\\''" == e.value.detail


class TestCommonParams:

    def test_one(self):
        """Test that we drop unique params"""

        c = CommonParams()
        c.add({"one": 1, "two": 2})
        c.add({"one": 1, "three": 3})
        c.add({"one": 1, "two": 5})
        assert {"one": 1} == c.render()


class TestList:

    @pytest.mark.parametrize(
        "input,output",
        (
            (None, []),
            (["a"], ["a"]),
            (["a", "b"], ["a", "b"]),
            (["a,b"], ["a", "b"]),
            (["a", "b,c", "d"], ["a", "b", "c", "d"]),
        ),
    )
    def test_split_empty(self, input, output):
        assert output == CrucibleService._split_list(input)


class TestFormatters:

    @pytest.mark.parametrize(
        "input",
        (
            "2024-09-12 18:29:35.123000+00:00",
            datetime.fromisoformat("2024-09-12 18:29:35.123000+00:00"),
            "1726165775123",
            1726165775123,
        ),
    )
    def test_normalize_date(self, input):
        assert 1726165775123 == CrucibleService._normalize_date(input)

    def test_normalize_date_bad(self):
        with pytest.raises(HTTPException) as e:
            CrucibleService._normalize_date([])
        assert 400 == e.value.status_code
        assert "Date representation [] is not a date string or timestamp"

    @pytest.mark.parametrize(
        "input,output",
        (
            ("abc", "1970-01-01 00:00:00+00:00"),
            ("1726165775123", "2024-09-12 18:29:35.123000+00:00"),
            (1726165775123, "2024-09-12 18:29:35.123000+00:00"),
        ),
    )
    def test_format_timestamp(self, input, output):
        assert output == CrucibleService._format_timestamp(input)

    def test_format_data(self):
        begin = 1726165775123
        duration = 10244
        raw = {
            "begin": str(begin),
            "end": str(begin + duration),
            "duration": str(duration),
            "value": "100.3",
        }
        expect = {
            "begin": "2024-09-12 18:29:35.123000+00:00",
            "end": "2024-09-12 18:29:45.367000+00:00",
            "duration": 10.244,
            "value": 100.3,
        }
        assert expect == CrucibleService._format_data(raw)

    def test_format_period(self):
        raw = {
            "begin": "1726165775123",
            "end": "1726165785234",
            "id": "ABC-123",
            "name": "measurement",
        }
        expect = {
            "begin": "2024-09-12 18:29:35.123000+00:00",
            "end": "2024-09-12 18:29:45.234000+00:00",
            "id": "ABC-123",
            "name": "measurement",
        }
        assert expect == CrucibleService._format_period(raw)


class TestHits:

    def test_no_hits(self):
        """Expect an exception because 'hits' is missing"""

        with pytest.raises(HTTPException) as e:
            for a in CrucibleService._hits({}):
                assert f"Unexpected result {type(a)}"
        assert 500 == e.value.status_code
        assert "Attempt to iterate hits for {}" == e.value.detail

    def test_empty_hits(self):
        """Expect successful iteration of no hits"""

        for a in CrucibleService._hits({"hits": {"hits": []}}):
            assert f"Unexpected result {a}"

    def test_hits(self):
        """Test that iteration through hits works"""

        expected = [{"a": 1}, {"b": 1}]
        payload = [{"_source": a} for a in expected]
        assert expected == list(CrucibleService._hits({"hits": {"hits": payload}}))

    def test_hits_fields(self):
        """Test that iteration through hit fields works"""

        expected = [{"a": 1}, {"b": 1}]
        payload = [{"_source": {"f": a, "e": 1}} for a in expected]
        assert expected == list(
            CrucibleService._hits({"hits": {"hits": payload}}, ["f"])
        )


class TestAggregates:

    def test_no_aggregations(self):
        """Expect an exception if the aggregations are missing"""
        with pytest.raises(HTTPException) as e:
            for a in CrucibleService._aggs({}, "agg"):
                assert f"Unexpected result {a}"
        assert 500 == e.value.status_code
        assert "Attempt to iterate missing aggregations for {}" == e.value.detail

    def test_missing_agg(self):
        """Expect an exception if the aggregations are missing"""

        payload = {"aggregations": {}}
        with pytest.raises(HTTPException) as e:
            for a in CrucibleService._aggs(payload, "agg"):
                assert f"Unexpected result {a}"
        assert 500 == e.value.status_code
        assert (
            f"Attempt to iterate missing aggregation 'agg' for {payload}"
            == e.value.detail
        )

    def test_empty_aggs(self):
        """Expect successful iteration of no aggregation data"""

        for a in CrucibleService._aggs(
            {"aggregations": {"agg": {"buckets": []}}}, "agg"
        ):
            assert f"Unexpected result {a}"

    def test_aggs(self):
        """Test that iteration through aggregations works"""

        expected = [{"key": 1, "doc_count": 2}, {"key": 2, "doc_count": 5}]
        payload = {
            "hits": {"total": {"value": 0}, "hits": []},
            "aggregations": {
                "agg": {
                    "buckets": [{"key": 1, "doc_count": 2}, {"key": 2, "doc_count": 5}]
                }
            },
        }
        assert expected == list(CrucibleService._aggs(payload, "agg"))


class TestFilterBuilders:

    @pytest.mark.parametrize(
        "filters,terms",
        (
            (
                ["param:v=1", "tag:x='one two'", "run:email='d@e.c'"],
                (
                    [
                        {
                            "dis_max": {
                                "queries": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "term": {
                                                        "param.arg": "v",
                                                    },
                                                },
                                                {
                                                    "term": {
                                                        "param.val": "1",
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    [
                        {
                            "dis_max": {
                                "queries": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "term": {
                                                        "tag.name": "x",
                                                    },
                                                },
                                                {
                                                    "term": {
                                                        "tag.val": "one two",
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    [
                        {
                            "term": {
                                "run.email": "d@e.c",
                            },
                        },
                    ],
                ),
            ),
            (
                ["param:v~a"],
                (
                    [
                        {
                            "dis_max": {
                                "queries": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "term": {
                                                        "param.arg": "v",
                                                    },
                                                },
                                                {
                                                    "regexp": {
                                                        "param.val": ".*a.*",
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    None,
                    None,
                ),
            ),
            (
                ["tag:v~a"],
                (
                    None,
                    [
                        {
                            "dis_max": {
                                "queries": [
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "term": {
                                                        "tag.name": "v",
                                                    },
                                                },
                                                {
                                                    "regexp": {
                                                        "tag.val": ".*a.*",
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    None,
                ),
            ),
        ),
    )
    def test_build_filter_options(self, filters, terms):
        assert terms == CrucibleService._build_filter_options(filters)

    def test_build_filter_bad_key(self):
        with pytest.raises(HTTPException) as e:
            CrucibleService._build_filter_options(["foobar:x=y"])
        assert 400 == e.value.status_code
        assert "unknown filter namespace 'foobar'" == e.value.detail

    def test_build_name_filters(self):
        assert [
            {"term": {"metric_desc.names.name": "1"}}
        ] == CrucibleService._build_name_filters(["name=1"])

    def test_build_name_filters_bad(self):
        with pytest.raises(HTTPException) as e:
            CrucibleService._build_name_filters(["xya:x"])
        assert 400 == e.value.status_code
        assert "Filter item 'xya:x' must be '<k>=<v>'"

    @pytest.mark.parametrize("periods", ([], ["10"], ["10", "20"]))
    def test_build_period_filters(self, periods):
        expected = (
            []
            if not periods
            else [
                {
                    "dis_max": {
                        "queries": [
                            {"bool": {"must_not": {"exists": {"field": "period"}}}},
                            {"terms": {"period.id": periods}},
                        ]
                    }
                }
            ]
        )
        assert expected == CrucibleService._build_period_filters(periods)

    @pytest.mark.parametrize(
        "term,message",
        (
            (
                "foo:asc",
                "Sort key 'foo' must be one of begin,benchmark,desc,email,end,harness,host,id,name,source",
            ),
            ("email:up", "Sort direction 'up' must be one of asc,desc"),
        ),
    )
    def test_build_sort_filters_error(self, term, message):
        with pytest.raises(HTTPException) as exc:
            CrucibleService._build_sort_terms([term])
        assert 400 == exc.value.status_code
        assert message == exc.value.detail

    @pytest.mark.parametrize(
        "sort,terms",
        (
            ([], (("run.begin", {"order": "asc"}),)),
            (["email:asc"], (("run.email", {"order": "asc"}),)),
            (
                ["email:desc", "name:asc"],
                (("run.email", {"order": "desc"}), ("run.name", {"order": "asc"})),
            ),
        ),
    )
    def test_build_sort_filters(self, sort, terms):
        expected = [{t[0]: t[1]} for t in terms]
        assert expected == CrucibleService._build_sort_terms(sort)

    @pytest.mark.parametrize(
        "periods,result",
        (
            (
                [
                    {
                        "period": {
                            "id": "one",
                            "begin": "1733505934677",
                            "end": "1733507347857",
                        }
                    }
                ],
                [
                    {"range": {"metric_data.begin": {"gte": "1733505934677"}}},
                    {"range": {"metric_data.end": {"lte": "1733507347857"}}},
                ],
            ),
            (None, []),
        ),
    )
    async def test_build_timestamp_filter(
        self, fake_crucible: CrucibleService, periods, result
    ):
        plist = None
        if periods:
            fake_crucible.elastic.set_query("period", periods)
            plist = [p["period"]["id"] for p in periods]
        assert result == await fake_crucible._build_timestamp_range_filters(plist)

    @pytest.mark.parametrize(
        "period,name",
        (
            ({"period": {"id": "one"}}, "run None:None,iteration None,sample None"),
            (
                {
                    "run": {"id": "rid", "benchmark": "test", "begin": "1234"},
                    "iteration": {"id": "iid", "num": 1},
                    "sample": {"id": "sid", "num": 1},
                    "period": {"id": "one", "begin": "5423"},
                },
                "run test:1234,iteration 1,sample 1",
            ),
        ),
    )
    async def test_build_timestamp_filter_bad(
        self, fake_crucible: CrucibleService, period, name
    ):
        fake_crucible.elastic.set_query("period", [period])
        with pytest.raises(HTTPException) as exc:
            await fake_crucible._build_timestamp_range_filters(["one"])
        assert 422 == exc.value.status_code
        assert (
            f"Unable to compute '{name}' time range: the run is missing period timestamps"
            == exc.value.detail
        )


class TestCrucible:

    async def test_create(self, fake_crucible):
        """Create and close a CrucibleService instance"""

        assert fake_crucible
        assert isinstance(fake_crucible, CrucibleService)
        assert isinstance(fake_crucible.elastic, AsyncElasticsearch)
        assert app.config.get_config().get("TEST.url") == fake_crucible.url
        elastic = fake_crucible.elastic
        await fake_crucible.close()
        assert fake_crucible.elastic is None
        assert elastic.closed

    async def test_search_args(self, fake_crucible: CrucibleService):
        await fake_crucible.search(
            "run",
            [{"term": "a"}],
            [{"x": {"field": "a"}}],
            [{"key": "asc"}],
            "run",
            42,
            69,
            x=2,
            z=3,
        )
        assert [
            Request(
                "cdmv7dev-run",
                {
                    "_source": "run",
                    "aggs": [
                        {
                            "x": {
                                "field": "a",
                            },
                        },
                    ],
                    "from": 69,
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": "a",
                                },
                            ],
                        },
                    },
                    "size": 42,
                    "sort": [
                        {
                            "key": "asc",
                        },
                    ],
                },
                None,
                None,
                None,
                {"x": 2, "z": 3},
            )
        ] == fake_crucible.elastic.requests

    async def test_metric_ids_none(self, fake_crucible):
        """A simple query for failure matching metric IDs"""

        fake_crucible.elastic.set_query("metric_desc", [])
        with pytest.raises(HTTPException) as e:
            await fake_crucible._get_metric_ids("runid", "source::type")
        assert 400 == e.value.status_code
        assert "No matches for source::type" == e.value.detail

    @pytest.mark.parametrize(
        "found,expected,aggregate",
        (
            (
                [
                    {"metric_desc": {"id": "one-metric"}},
                ],
                ["one-metric"],
                False,
            ),
            (
                [
                    {"metric_desc": {"id": "one-metric"}},
                ],
                ["one-metric"],
                True,
            ),
            (
                [
                    {"metric_desc": {"id": "one-metric"}},
                    {"metric_desc": {"id": "two-metric"}},
                ],
                ["one-metric", "two-metric"],
                True,
            ),
        ),
    )
    async def test_metric_ids(self, fake_crucible, found, expected, aggregate):
        """A simple query for matching metric IDs"""

        fake_crucible.elastic.set_query("metric_desc", found)
        assert expected == await fake_crucible._get_metric_ids(
            "runid",
            "source::type",
            aggregate=aggregate,
        )

    @pytest.mark.parametrize(
        "found,message",
        (
            (
                [
                    {"metric_desc": {"id": "one-metric", "names": {"john": "yes"}}},
                    {"metric_desc": {"id": "two-metric", "names": {"john": "no"}}},
                ],
                (2, [], {"john": ["no", "yes"]}),
            ),
            (
                [
                    {
                        "period": {"id": "p1"},
                        "metric_desc": {"id": "three-metric", "names": {"john": "yes"}},
                    },
                    {"metric_desc": {"id": "four-metric", "names": {"fred": "why"}}},
                    {
                        "period": {"id": "p2"},
                        "metric_desc": {"id": "five-metric", "names": {"john": "sure"}},
                    },
                    {"metric_desc": {"id": "six-metric", "names": {"john": "maybe"}}},
                ],
                (4, ["p1", "p2"], {"john": ["maybe", "sure", "yes"]}),
            ),
        ),
    )
    async def test_metric_ids_unproc(self, fake_crucible, found, message):
        """Test matching metric IDs with lax criteria"""

        fake_crucible.elastic.set_query("metric_desc", found)
        with pytest.raises(HTTPException) as exc:
            await fake_crucible._get_metric_ids(
                "runid",
                "source::type",
                aggregate=False,
            )
        assert 422 == exc.value.status_code
        assert {
            "message": f"More than one metric ({message[0]}) means you should add breakout filters or aggregate.",
            "periods": message[1],
            "names": message[2],
        } == exc.value.detail

    async def test_run_filters(self, fake_crucible):
        """Test aggregations

        This is the "simplest" aggregation-based query, but we need to define
        fake aggregations for the tag, param, and run indices.
        """

        fake_crucible.elastic.set_query(
            "tag",
            aggregations={
                "key": [
                    {
                        "key": "topology",
                        "doc_count": 25,
                        "values": {
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                            "buckets": [],
                        },
                    },
                    {
                        "key": "accelerator",
                        "doc_count": 19,
                        "values": {
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                            "buckets": [
                                {"key": "A100", "doc_count": 5},
                                {"key": "L40S", "doc_count": 2},
                            ],
                        },
                    },
                    {
                        "key": "project",
                        "doc_count": 19,
                        "values": {
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                            "buckets": [
                                {"key": "rhelai", "doc_count": 1},
                                {"key": "rhosai", "doc_count": 2},
                            ],
                        },
                    },
                ]
            },
        )
        fake_crucible.elastic.set_query(
            "param",
            aggregations={
                "key": [
                    {
                        "key": "bucket",
                        "doc_count": 25,
                        "values": {
                            "doc_count_error_upper_bound": 0,
                            "sum_other_doc_count": 0,
                            "buckets": [{"key": 200, "doc_count": 30}],
                        },
                    },
                ]
            },
        )
        fake_crucible.elastic.set_query(
            "run",
            aggregations={
                "begin": [{"key": 123456789, "doc_count": 1}],
                "benchmark": [{"key": "ilab", "doc_count": 25}],
                "desc": [],
                "email": [
                    {"key": "me@example.com", "doc_count": 10},
                    {"key": "you@example.com", "doc_count": 15},
                ],
                "end": [{"key": 1234, "doc_count": 10}],
                "harness": [],
                "host": [
                    {"key": "one.example.com", "doc_count": 5},
                    {"key": "two.example.com", "doc_count": 20},
                ],
                "id": [],
                "name": [],
                "source": [],
            },
        )
        filters = await fake_crucible.get_run_filters()

        # Array ordering is not reliable, so we need to sort
        assert sorted(filters.keys()) == ["param", "run", "tag"]
        assert sorted(filters["tag"].keys()) == ["accelerator", "project"]
        assert sorted(filters["param"].keys()) == ["bucket"]
        assert sorted(filters["run"].keys()) == ["benchmark", "email", "host"]
        assert sorted(filters["tag"]["accelerator"]) == ["A100", "L40S"]
        assert sorted(filters["param"]["bucket"]) == [200]
        assert sorted(filters["run"]["benchmark"]) == ["ilab"]
        assert sorted(filters["run"]["email"]) == ["me@example.com", "you@example.com"]
        assert sorted(filters["run"]["host"]) == ["one.example.com", "two.example.com"]

    async def test_get_run_ids(self, fake_crucible: CrucibleService):
        """_get_run_ids

        This is just straightline code coverage as there's no point in mocking
        the filters.
        """
        fake_crucible.elastic.set_query(
            "period",
            [{"run": {"id": "one"}}, {"run": {"id": "two"}}, {"run": {"id": "three"}}],
        )
        assert {"one", "two", "three"} == await fake_crucible._get_run_ids(
            "period", [{"term": {"period.name": "measurement"}}]
        )

    async def test_get_runs_none(self, fake_crucible: CrucibleService):
        """Test run summary"""
        fake_crucible.elastic.set_query("run", [])
        fake_crucible.elastic.set_query("iteration", [])
        fake_crucible.elastic.set_query("tag", [])
        fake_crucible.elastic.set_query("param", [])
        assert {
            "count": 0,
            "offset": 0,
            "results": [],
            "sort": [],
            "total": 0,
        } == await fake_crucible.get_runs()

    async def test_get_runs_time_reverse(self, fake_crucible: CrucibleService):
        """Test run summary"""
        fake_crucible.elastic.set_query("run", [])
        fake_crucible.elastic.set_query("iteration", [])
        fake_crucible.elastic.set_query("tag", [])
        fake_crucible.elastic.set_query("param", [])
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_runs(start="2025-01-01", end="2024-01-01")
        assert 422 == exc.value.status_code
        assert {
            "error": "Invalid date format, start_date must be less than end_date"
        } == exc.value.detail

    @pytest.mark.parametrize(
        "args,miss,notag,noparam",
        (
            ({}, False, False, False),
            ({"size": 2, "offset": 1}, False, False, False),
            ({"start": "2024-01-01"}, False, False, False),
            ({"end": "2024-02-01"}, False, False, False),
            ({"start": "2024-01-01", "end": "2025-01-01"}, False, False, False),
            ({"sort": ["end:desc"]}, False, False, False),
            (
                {"filter": ["tag:a=42", "param:z=xyzzy", "run:benchmark=test"]},
                False,
                False,
                False,
            ),
            ({"filter": ["tag:a=42", "param:z=xyzzy"]}, True, False, False),
            ({"filter": ["tag:a=42", "param:z=xyzzy"]}, False, True, False),
            ({"filter": ["tag:a=42", "param:z=xyzzy"]}, False, False, True),
        ),
    )
    async def test_get_runs_queries(
        self, args, miss, notag, noparam, fake_crucible: CrucibleService
    ):
        """Test processing of various query parameters

        Note, this isn't really testing "behavior" of the filters, which is all
        in Opensearch, just the CPT service's handling of the query parameters.

        TBD: This should really verify the generated Opensearch query filters,
        although that's mostly covered by earlier tests.
        """
        runs = [
            {"run": {"id": "r1", "begin": "0", "end": "5000", "benchmark": "test"}},
        ]
        if miss:
            # Add additional runs which will be rejected by filters
            runs.extend(
                [
                    {
                        "run": {
                            "id": "r2",
                            "begin": "110",
                            "end": "7000",
                            "benchmark": "test",
                        }
                    },
                    {
                        "run": {
                            "id": "r3",
                            "begin": "110",
                            "end": "6000",
                            "benchmark": "test",
                        }
                    },
                ]
            )
        fake_crucible.elastic.set_query("run", runs)
        fake_crucible.elastic.set_query(
            "iteration",
            [
                {
                    "run": {"id": "r1"},
                    "iteration": {
                        "id": "i1",
                        "num": 1,
                        "primary-period": "tp",
                        "primary-metric": "src::tst1",
                        "status": "pass",
                    },
                },
                {
                    "run": {"id": "r1"},
                    "iteration": {
                        "id": "i2",
                        "num": 2,
                        "primary-period": "tp",
                        "primary-metric": "src::tst2",
                        "status": "pass",
                    },
                },
                {
                    "run": {"id": "r1"},
                    "iteration": {
                        "id": "i3",
                        "num": 3,
                        "primary-period": "tp",
                        "primary-metric": "src::tst1",
                        "status": "fail",
                    },
                },
            ],
        )

        if notag:
            tags = []
        else:
            tags = [
                {"run": {"id": "r1"}, "tag": {"name": "a", "val": 42}},
                {"run": {"id": "r2"}, "tag": {"name": "a", "val": 42}},
            ]
        fake_crucible.elastic.set_query("tag", tags, repeat=2)

        if noparam:
            params = []
        else:
            params = [
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i1"},
                    "param": {"arg": "b", "val": "cde"},
                },
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i1"},
                    "param": {"arg": "z", "val": "xyzzy"},
                },
                {
                    "run": {"id": "r3"},
                    "iteration": {"id": "i1"},
                    "param": {"arg": "z", "val": "xyzzy"},
                },
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i2"},
                    "param": {"arg": "b", "val": "cde"},
                },
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i2"},
                    "param": {"arg": "x", "val": "plugh"},
                },
            ]
        fake_crucible.elastic.set_query("param", params, repeat=2)
        expected = {
            "count": 1,
            "offset": 0,
            "results": [
                {
                    "begin": "0",
                    "begin_date": "1970-01-01 00:00:00+00:00",
                    "benchmark": "test",
                    "end": "5000",
                    "end_date": "1970-01-01 00:00:05+00:00",
                    "id": "r1",
                    "iterations": [
                        {
                            "iteration": 1,
                            "params": defaultdict(
                                None,
                                {
                                    "b": "cde",
                                    "z": "xyzzy",
                                },
                            ),
                            "primary_metric": "src::tst1",
                            "primary_period": "tp",
                            "status": "pass",
                        },
                        {
                            "iteration": 2,
                            "params": defaultdict(
                                None,
                                {
                                    "b": "cde",
                                    "x": "plugh",
                                },
                            ),
                            "primary_metric": "src::tst2",
                            "primary_period": "tp",
                            "status": "pass",
                        },
                        {
                            "iteration": 3,
                            "params": {},
                            "primary_metric": "src::tst1",
                            "primary_period": "tp",
                            "status": "fail",
                        },
                    ],
                    "params": {},
                    "primary_metrics": {"src::tst1", "src::tst2"},
                    "status": "fail",
                    "tags": defaultdict(None, {"a": 42}),
                },
            ],
            "sort": [],
            "total": 1,
        }
        if notag or noparam:
            expected["results"] = []
            expected["count"] = 0
            expected["total"] = 0
        else:
            if miss:
                expected["total"] = 3
        if "size" in args:
            expected["size"] = args["size"]
        if args.get("offset"):
            expected["offset"] = args["offset"]
        if args.get("start"):
            expected["startDate"] = (
                datetime.fromisoformat(args["start"])
                .astimezone(tz=timezone.utc)
                .isoformat()
            )
        if args.get("end"):
            expected["endDate"] = (
                datetime.fromisoformat(args["end"])
                .astimezone(tz=timezone.utc)
                .isoformat()
            )
        if args.get("sort"):
            expected["sort"] = args["sort"]
        assert expected == await fake_crucible.get_runs(**args)

    async def test_get_tags(self, fake_crucible: CrucibleService):
        """Get tags for a run ID"""
        fake_crucible.elastic.set_query(
            "tag",
            [
                {"run": {"id": "one"}, "tag": {"name": "a", "val": 123}},
                {"run": {"id": "one"}, "tag": {"name": "b", "val": "hello"}},
                {"run": {"id": "one"}, "tag": {"name": "c", "val": False}},
            ],
        )
        assert {"a": 123, "b": "hello", "c": False} == await fake_crucible.get_tags(
            "one"
        )

    async def test_get_params_none(self, fake_crucible: CrucibleService):
        """Test error when neither run nor iteration is specified"""
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_params()
        assert 400 == exc.value.status_code
        assert (
            "A params query requires either a run or iteration ID" == exc.value.detail
        )

    async def test_get_params_run(self, fake_crucible: CrucibleService):
        """Get parameters for a run"""
        params = [
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "b", "val": 5},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "c", "val": "val"},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid2"},
                "param": {"arg": "a", "val": 7},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid2"},
                "param": {"arg": "c", "val": "val"},
            },
        ]
        fake_crucible.elastic.set_query("param", params)
        assert {
            "common": {"c": "val"},
            "iid1": {"a": 10, "b": 5, "c": "val"},
            "iid2": {"a": 7, "c": "val"},
        } == await fake_crucible.get_params("rid")

    async def test_get_params_iteration(self, fake_crucible: CrucibleService):
        """Get parameters for an iteration"""
        params = [
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "b", "val": 5},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "c", "val": "val"},
            },
        ]
        fake_crucible.elastic.set_query("param", params)
        assert {
            "iid1": {"a": 10, "b": 5, "c": "val"}
        } == await fake_crucible.get_params(None, "iid1")

    async def test_get_params_iteration_dup(self, fake_crucible: CrucibleService):
        """Cover an obscure log warning case"""
        params = [
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"id": "rid"},
                "iteration": {"id": "iid1"},
                "param": {"arg": "a", "val": 5},
            },
        ]
        fake_crucible.elastic.set_query("param", params)
        assert {"iid1": {"a": 5}} == await fake_crucible.get_params(None, "iid1")

    async def test_get_iterations(self, fake_crucible: CrucibleService):
        """Get iterations for a run ID"""
        iterations = [
            {
                "id": "one",
                "num": 1,
                "path": None,
                "primary_metric": "test::metric1",
                "primary_period": "measurement",
                "status": "pass",
            },
            {
                "id": "two",
                "num": 2,
                "path": None,
                "primary_metric": "test::metric2",
                "primary_period": "measurement",
                "status": "pass",
            },
            {
                "id": "three",
                "num": 3,
                "path": None,
                "primary_metric": "test::metric1",
                "primary_period": "measurement",
                "status": "pass",
            },
        ]
        fake_crucible.elastic.set_query(
            "iteration",
            [
                {
                    "run": {"id": "one"},
                    "iteration": i,
                }
                for i in iterations
            ],
        )
        assert iterations == await fake_crucible.get_iterations("one")

    async def test_get_samples_none(self, fake_crucible: CrucibleService):
        """Test error when neither run nor iteration is specified"""
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_samples()
        assert 400 == exc.value.status_code
        assert (
            "A sample query requires either a run or iteration ID" == exc.value.detail
        )

    @pytest.mark.parametrize("ids", (("one", None), (None, 1)))
    async def test_get_samples(self, fake_crucible: CrucibleService, ids):
        """Get samples for a run ID"""
        samples = [
            {
                "num": "1",
                "path": None,
                "id": "one",
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
            {
                "id": "two",
                "num": "2",
                "path": None,
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
            {
                "id": "three",
                "num": "3",
                "path": None,
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
        ]
        fake_crucible.elastic.set_query(
            "sample",
            [
                {
                    "run": {"id": "one"},
                    "iteration": {
                        "primary-metric": "pm",
                        "primary-period": "m",
                        "num": 1,
                    },
                    "sample": s,
                }
                for s in samples
            ],
        )
        assert samples == await fake_crucible.get_samples(*ids)

    async def test_get_periods_none(self, fake_crucible: CrucibleService):
        """Test error when neither run, iteration, nor sample is specified"""
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_periods()
        assert 400 == exc.value.status_code
        assert (
            "A period query requires a run, iteration, or sample ID" == exc.value.detail
        )

    @pytest.mark.parametrize(
        "ids", (("one", None, None), (None, 1, None), (None, None, 1))
    )
    async def test_get_periods(self, fake_crucible: CrucibleService, ids):
        """Get samples for a run ID"""
        periods = [
            {
                "begin": "2024-12-05 21:16:31.046000+00:00",
                "end": "2024-12-05 21:40:31.166000+00:00",
                "id": "306C8A78-B352-11EF-8E37-AD212D0A0B9F",
                "name": "measurement",
                "iteration": 1,
                "sample": 1,
                "primary_metric": "ilab::sdg-samples-sec",
                "status": "pass",
            }
        ]
        fake_crucible.elastic.set_query(
            "period",
            [
                {
                    "run": {"id": "one"},
                    "iteration": {
                        "primary-metric": p["primary_metric"],
                        "primary-period": "measurement",
                        "num": 1,
                        "status": p["status"],
                    },
                    "sample": {"num": 1, "status": p["status"], "path": None},
                    "period": {
                        "id": p["id"],
                        "name": p["name"],
                        "begin": str(
                            int(datetime.fromisoformat(p["begin"]).timestamp() * 1000)
                        ),
                        "end": str(
                            int(datetime.fromisoformat(p["end"]).timestamp() * 1000)
                        ),
                        "primary-metric": p["primary_metric"],
                        "status": p["status"],
                    },
                }
                for p in periods
            ],
        )
        assert periods == await fake_crucible.get_periods(*ids)

    async def test_get_metrics_list(self, fake_crucible: CrucibleService):
        """Get samples for a run ID"""
        metrics = {
            "source1::type1": {
                "periods": [],
                "breakouts": {"name1": ["value1", "value2"]},
            },
            "source1::type2": {"periods": ["p1", "p2"], "breakouts": {}},
        }
        query = [
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value2"},
                },
            },
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value2"},
                },
            },
            {
                "run": {"id": "one"},
                "period": {"id": "p1"},
                "metric_desc": {"source": "source1", "type": "type2", "names": {}},
            },
            {
                "run": {"id": "one"},
                "period": {"id": "p2"},
                "metric_desc": {"source": "source1", "type": "type2", "names": {}},
            },
        ]
        fake_crucible.elastic.set_query("metric_desc", query)
        result = await fake_crucible.get_metrics_list("one")

        # NOTE: the method returns a defaultdict, which doesn't compare to a
        # dict but "in the real world" serializes the same: so we just
        # serialize and deserialize to mimic the actual API behavior.
        result = json.loads(json.dumps(result))
        assert metrics == result

    async def test_get_metric_breakout_none(self, fake_crucible: CrucibleService):
        """Test error when the metric isn't found"""
        fake_crucible.elastic.set_query("metric_desc", [])
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_metric_breakouts(
                "one", metric="source1::type1", names=[], periods=[]
            )
        assert 400 == exc.value.status_code
        assert "Metric name source1::type1 not found for run one" == exc.value.detail

    @pytest.mark.parametrize("period", (True, False))
    async def test_get_metric_breakout(self, period, fake_crucible: CrucibleService):
        """Get samples for a run ID"""
        metrics = {
            "label": "source1::type1",
            "class": ["classless", "classy"],
            "type": "type1",
            "source": "source1",
            "breakouts": {"name1": ["value1", "value2"]},
        }
        md1 = {
            "run": {"id": "one"},
            "metric_desc": {
                "source": "source1",
                "type": "type1",
                "class": "classy",
                "names": {"name1": "value1"},
            },
        }
        md2 = {
            "run": {"id": "one"},
            "metric_desc": {
                "source": "source1",
                "type": "type1",
                "names": {"name1": "value2"},
            },
        }
        if period:
            metrics["periods"] = ["p1", "p2"]
            md1["period"] = {"id": "p1"}
            md2["period"] = {"id": "p2"}
        query = [
            md1,
            md2,
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "class": "classless",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"id": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value2"},
                },
            },
        ]
        fake_crucible.elastic.set_query("metric_desc", query)
        result = await fake_crucible.get_metric_breakouts(
            "one", metric="source1::type1", names=[], periods=[]
        )

        # NOTE: the method returns a defaultdict, which doesn't compare to a
        # dict but "in the real world" serializes the same: so we just
        # serialize and deserialize to mimic the actual API behavior.
        result = json.loads(json.dumps(result))
        assert metrics == result

    async def test_metrics_data_one_noagg(self, fake_crucible: CrucibleService):
        """Return data samples for a single metric"""

        fake_crucible.elastic.set_query(
            "metric_desc",
            [{"metric_desc": {"id": "one-metric", "names": {}}}],
        )
        fake_crucible.elastic.set_query(
            "metric_data",
            [
                {
                    "metric_desc": {"id": "one-metric"},
                    "metric_data": {
                        "begin": "1726165775123",
                        "end": "1726165789213",
                        "duration": 14100,
                        "value": 9.35271216694379,
                    },
                },
                {
                    "metric_desc": {"id": "one-metric"},
                    "metric_data": {
                        "begin": "1726165790000",
                        "end": "1726165804022",
                        "duration": 14022,
                        "value": 9.405932330557683,
                    },
                },
            ],
        )
        expected = [
            {
                "begin": "2024-09-12 18:29:35.123000+00:00",
                "duration": 14.1,
                "end": "2024-09-12 18:29:49.213000+00:00",
                "value": 9.35271216694379,
            },
            {
                "begin": "2024-09-12 18:29:50+00:00",
                "duration": 14.022,
                "end": "2024-09-12 18:30:04.022000+00:00",
                "value": 9.405932330557683,
            },
        ]
        assert expected == await fake_crucible.get_metrics_data("runid", "source::type")
        assert fake_crucible.elastic.requests == [
            Request(
                "cdmv7dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "runid",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.source": "source",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.type": "type",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
                kwargs={"ignore_unavailable": True},
            ),
            Request(
                "cdmv7dev-metric_data",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.id": [
                                            "one-metric",
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
            ),
        ]

    @pytest.mark.parametrize("count", (0, 2))
    async def test_metrics_data_agg(self, count, fake_crucible):
        """Return data samples for aggregated metrics"""

        fake_crucible.elastic.set_query(
            "metric_desc",
            [
                {"metric_desc": {"id": "one-metric", "names": {}}},
                {"metric_desc": {"id": "two-metric", "names": {}}},
            ],
        )
        fake_crucible.elastic.set_query(
            "metric_data",
            aggregations={
                "duration": {
                    "count": count,
                    "min": 14022,
                    "max": 14100,
                    "avg": 14061,
                    "sum": 28122,
                }
            },
        )
        if count:
            fake_crucible.elastic.set_query(
                "metric_data",
                aggregations={
                    "interval": [
                        {"key": 1726165789213, "value": {"value": 9.35271216694379}},
                        {"key": 1726165804022, "value": {"value": 9.405932330557683}},
                    ]
                },
            )
            expected = [
                {
                    "begin": "2024-09-12 18:29:35.191000+00:00",
                    "duration": 14.022,
                    "end": "2024-09-12 18:29:49.213000+00:00",
                    "value": 9.35271216694379,
                },
                {
                    "begin": "2024-09-12 18:29:50+00:00",
                    "duration": 14.022,
                    "end": "2024-09-12 18:30:04.022000+00:00",
                    "value": 9.405932330557683,
                },
            ]
        else:
            expected = []
        assert expected == await fake_crucible.get_metrics_data(
            "r1", "source::type", aggregate=True
        )
        expected_requests = [
            Request(
                "cdmv7dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "r1",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.source": "source",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.type": "type",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
                kwargs={"ignore_unavailable": True},
            ),
            Request(
                "cdmv7dev-metric_data",
                {
                    "aggs": {
                        "duration": {
                            "stats": {
                                "field": "metric_data.duration",
                            },
                        },
                    },
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.id": [
                                            "one-metric",
                                            "two-metric",
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                    "size": 0,
                },
            ),
        ]
        if count:
            expected_requests.append(
                Request(
                    "cdmv7dev-metric_data",
                    {
                        "aggs": {
                            "interval": {
                                "aggs": {
                                    "value": {
                                        "sum": {
                                            "field": "metric_data.value",
                                        },
                                    },
                                },
                                "histogram": {
                                    "field": "metric_data.end",
                                    "interval": 14022,
                                },
                            },
                        },
                        "query": {
                            "bool": {
                                "filter": [
                                    {
                                        "terms": {
                                            "metric_desc.id": [
                                                "one-metric",
                                                "two-metric",
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                        "size": 0,
                    },
                ),
            )
        assert fake_crucible.elastic.requests == expected_requests

    async def test_metrics_summary(self, fake_crucible: CrucibleService):
        """Return data summary for a metrics"""

        fake_crucible.elastic.set_query(
            "metric_desc",
            [
                {"metric_desc": {"id": "one-metric", "names": {"a": "1"}}},
            ],
        )
        expected = {
            "count": 5,
            "min": 9.35271216694379,
            "max": 9.405932330557683,
            "avg": 9.379322249,
            "sum": 18.758644498,
        }
        fake_crucible.elastic.set_query("metric_data", aggregations={"score": expected})
        assert expected == await fake_crucible.get_metrics_summary(
            "runid", "one-metric::type", ["a=1"]
        )
        assert fake_crucible.elastic.requests == [
            Request(
                "cdmv7dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "runid",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.source": "one-metric",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.type": "type",
                                    },
                                },
                                {"term": {"metric_desc.names.a": "1"}},
                            ],
                        },
                    },
                    "size": 262144,
                },
                kwargs={"ignore_unavailable": True},
            ),
            Request(
                "cdmv7dev-metric_data",
                {
                    "aggs": {"score": {"stats": {"field": "metric_data.value"}}},
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.id": [
                                            "one-metric",
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                    "size": 0,
                },
            ),
        ]

    @pytest.mark.parametrize(
        "runs,param_idx,periods,period_idx,title",
        (
            ([], 0, [], 0, "source::type"),
            (["r2", "r1"], 0, [], 0, "source::type {run 2}"),
            ([], 0, ["p1"], 0, "source::type (n=42)"),
            ([], 1, ["p1"], 1, "source::type"),
            ([], 1, ["p1"], 2, "source::type"),
        ),
    )
    async def test_graph_title_no_query(
        self,
        runs,
        param_idx,
        periods,
        period_idx,
        title,
        fake_crucible: CrucibleService,
    ):
        """Test generation of default metric titles"""

        param_runs = [
            {"r1": {"i1": {"n": "42"}, "i2": {"n": "31"}}},
            {"r1": {"i1": {"n": "42"}, "i2": {"n": "42"}}},
        ][param_idx]
        period_runs = [
            {"r1": {"i1": {"p1"}, "i2": {"p2"}}},
            {"r1": {"i1": {"p1"}}},
            {"r1": {"i1": {"p2"}}},
        ][period_idx]
        name = await fake_crucible._graph_title(
            "r1",
            runs,
            Graph(metric="source::type", periods=periods),
            param_runs,
            period_runs,
        )
        assert name == title

    async def test_graph_title_query(self, fake_crucible: CrucibleService):
        """Test generation of default metric titles"""

        param_runs = {}
        period_runs = {}
        fake_crucible.elastic.set_query(
            "param",
            [
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i1"},
                    "param": {"arg": "a", "val": "1"},
                },
            ],
        )
        fake_crucible.elastic.set_query(
            "period",
            [
                {
                    "run": {"id": "r1"},
                    "iteration": {"id": "i1"},
                    "period": {"id": "p1"},
                },
            ],
        )
        name = await fake_crucible._graph_title(
            "r1",
            [],
            Graph(metric="source::type"),
            param_runs,
            period_runs,
        )
        assert name == "source::type"
        assert fake_crucible.elastic.requests == [
            Request(
                "cdmv7dev-param",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "r1",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
            ),
            Request(
                "cdmv7dev-period",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "r1",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
            ),
        ]

    async def test_metrics_graph_norun(self, fake_crucible: CrucibleService):
        with pytest.raises(HTTPException) as exc:
            await fake_crucible.get_metrics_graph(
                GraphList(
                    name="graph",
                    graphs=[Graph(metric="source::type", aggregate=True, title="test")],
                )
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == "each graph request must have a run ID"

    @pytest.mark.parametrize("count", (0, 2))
    async def test_metrics_graph(self, count, fake_crucible: CrucibleService):
        """Return graph for aggregated metrics"""

        metrics = [{"metric_desc": {"id": "one-metric", "names": {}}}]
        if count:
            metrics.append({"metric_desc": {"id": "two-metric", "names": {}}})
            fake_crucible.elastic.set_query(
                "metric_data",
                aggregations={
                    "duration": {
                        "count": count,
                        "min": 14022,
                        "max": 14100,
                        "avg": 14061,
                        "sum": 28122,
                    }
                },
            )
            fake_crucible.elastic.set_query(
                "metric_data",
                aggregations={
                    "interval": [
                        {"key": 1726165789213, "value": {"value": 9.35271216694379}},
                        {"key": 1726165804022, "value": {"value": 9.405932330557683}},
                    ]
                },
            )
            expected = {
                "data": [
                    {
                        "labels": {
                            "x": "sample timestamp",
                            "y": "samples / second",
                        },
                        "marker": {
                            "color": "black",
                        },
                        "mode": "line",
                        "name": "test",
                        "type": "scatter",
                        "x": [
                            "2024-09-12 18:29:49.213000+00:00",
                            "2024-09-12 18:30:03.234000+00:00",
                            "2024-09-12 18:30:04.022000+00:00",
                            "2024-09-12 18:30:18.043000+00:00",
                        ],
                        "y": [
                            9.35271216694379,
                            9.35271216694379,
                            9.405932330557683,
                            9.405932330557683,
                        ],
                        "yaxis": "y",
                    },
                ],
                "layout": {
                    "width": "1500",
                    "yaxis": {
                        "color": "black",
                        "title": "source::type",
                    },
                },
            }
        else:
            expected = {
                "data": [
                    {
                        "labels": {
                            "x": "sample timestamp",
                            "y": "samples / second",
                        },
                        "marker": {
                            "color": "black",
                        },
                        "mode": "line",
                        "name": "test",
                        "type": "scatter",
                        "x": [
                            "2024-09-12 18:29:49.213000+00:00",
                            "2024-09-12 18:29:50.213000+00:00",
                            "2024-09-12 18:30:04.022000+00:00",
                            "2024-09-12 18:30:05.022000+00:00",
                        ],
                        "y": [
                            9.35271216694379,
                            9.35271216694379,
                            9.405932330557683,
                            9.405932330557683,
                        ],
                        "yaxis": "y",
                    },
                ],
                "layout": {
                    "width": "1500",
                    "yaxis": {
                        "color": "black",
                        "title": "source::type",
                    },
                },
            }
            fake_crucible.elastic.set_query(
                "metric_data",
                [
                    {
                        "metric_data": {
                            "begin": "1726165789213",
                            "end": "1726165790213",
                            "value": 9.35271216694379,
                        }
                    },
                    {
                        "metric_data": {
                            "begin": "1726165804022",
                            "end": "1726165805022",
                            "value": 9.405932330557683,
                        }
                    },
                ],
            )
        fake_crucible.elastic.set_query("metric_desc", metrics)

        assert expected == await fake_crucible.get_metrics_graph(
            GraphList(
                run="r1",
                name="graph",
                graphs=[Graph(metric="source::type", aggregate=True, title="test")],
            )
        )
        expected_requests = [
            Request(
                "cdmv7dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.id": "r1",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.source": "source",
                                    },
                                },
                                {
                                    "term": {
                                        "metric_desc.type": "type",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
                kwargs={"ignore_unavailable": True},
            ),
        ]
        if count:
            expected_requests.extend(
                [
                    Request(
                        "cdmv7dev-metric_data",
                        {
                            "aggs": {
                                "duration": {
                                    "stats": {
                                        "field": "metric_data.duration",
                                    },
                                },
                            },
                            "query": {
                                "bool": {
                                    "filter": [
                                        {
                                            "terms": {
                                                "metric_desc.id": [
                                                    "one-metric",
                                                    "two-metric",
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                            "size": 0,
                        },
                    ),
                    Request(
                        "cdmv7dev-metric_data",
                        {
                            "aggs": {
                                "interval": {
                                    "aggs": {
                                        "value": {
                                            "sum": {
                                                "field": "metric_data.value",
                                            },
                                        },
                                    },
                                    "histogram": {
                                        "field": "metric_data.begin",
                                        "interval": 14022,
                                    },
                                },
                            },
                            "query": {
                                "bool": {
                                    "filter": [
                                        {
                                            "terms": {
                                                "metric_desc.id": [
                                                    "one-metric",
                                                    "two-metric",
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                            "size": 0,
                        },
                    ),
                ]
            )
        else:
            expected_requests.append(
                Request(
                    "cdmv7dev-metric_data",
                    {
                        "query": {
                            "bool": {
                                "filter": [
                                    {
                                        "terms": {
                                            "metric_desc.id": ["one-metric"],
                                        },
                                    },
                                ],
                            },
                        },
                        "size": 262144,
                    },
                ),
            )
        assert fake_crucible.elastic.requests == expected_requests
