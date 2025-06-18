from datetime import datetime, timezone
import json

from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
import pytest

import app.config
from app.services.crucible_svc import (
    CommonParams,
    CrucibleService,
    DataDTO,
    FullID,
    GraphList,
    IterationDTO,
    Metric,
    MetricDTO,
    Parser,
    PeriodDTO,
    RunDTO,
    SampleDTO,
)
from tests.unit.fake_elastic import Request


class TestParser:

    def test_parse_normal(self):
        """Test successful parsing of three terms"""

        t = Parser("foo:bar=x")
        assert ("foo", ":") == t._next_token([":", "="])
        assert ("bar", "=") == t._next_token([":", "="])
        assert ("x", None) == t._next_token([":", "="], optional=True)

    def test_parse_missing(self):
        """Test exception when a required delimiter is not found"""

        t = Parser("foo:bar=x")
        assert ("foo", ":") == t._next_token([":", "="])
        assert ("bar", "=") == t._next_token([":", "="])
        # Without optional=True, expect exception after exhausting the term
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
    def test_split_list(self, input, output):
        assert output == CrucibleService._split_list(input)

    @pytest.mark.parametrize(
        "input,output",
        (
            (None, []),
            (["a"], [FullID("a")]),
            (["a@v9dev@2024.10"], [FullID("a", "v9dev", "2024.10")]),
            (["a", "b"], [FullID("a"), FullID("b")]),
            (["a@v8dev@2025.02,b"], [FullID("a", "v8dev", "2025.02"), FullID("b")]),
            (["a", "b,c", "d"], [FullID("a"), FullID("b"), FullID("c"), FullID("d")]),
        ),
    )
    def test_split_id_list(self, input, output):
        assert output == CrucibleService._split_id_list(input)


class TestFullID:

    @pytest.mark.parametrize(
        "params,string",
        (
            (("abc", "v9dev", "2025.05"), "abc@v9dev@2025.05"),
            (("abc", None, None), "abc"),
            (("abc", "v9dev", None), "abc@v9dev@"),
            (("abc", None, "2025.05"), "abc@@2025.05"),
        ),
    )
    def test_create(self, params, string):
        full = FullID(*params)
        assert full.render() == string

        render = FullID.decode(string)
        assert render == full

    def test_idempotent(self):
        """Decoding a FullID returns the FullID"""
        full_id = FullID("abc", "v9dev", "2025.05")
        assert full_id == FullID.decode(full_id)


class TestDTOs:

    def test_run_dto_bad(self):
        """Try to build a DTO with a bad document"""
        with pytest.raises(HTTPException) as exc:
            RunDTO({"foo": {}, "cdm": {"ver": "v8dev"}})
        assert 500 == exc.value.status_code
        assert (
            "Raw CDM object is missing required keys: ['run'] not in ['cdm', 'foo']"
            == exc.value.detail
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-run", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-run@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_run_dto(self, version, index, full_id):
        body = {
            "benchmark": "test",
            "email": "test@example.com",
            "name": "CI",
            "source": "cdm.example.com/var/lib/abc",
        }
        source = {
            "cdm": {"ver": version},
            "run": body
            | {
                "run-uuid": "foobar",
                "begin": "1726162827982",
                "end": "1726164203132",
                "host": "foobar@plugh.dnd",
            },
        }
        if index:
            source = {"_index": index, "_source": source}
        run = RunDTO(source)
        assert run.uuid == "foobar"
        assert run.version == version
        assert (
            body
            | {
                "id": full_id if full_id else "foobar",
                "uuid": "foobar",
                "begin": 1726162827982,
                "begin_date": "2024-09-12 17:40:27.982000+00:00",
                "end": 1726164203132,
                "end_date": "2024-09-12 18:03:23.132000+00:00",
                "iterations": [],
                "params": {},
                "primary_metrics": [],
                "status": None,
                "host": "foobar@plugh.dnd",
                "harness": None,
                "tags": {},
            }
            == run.json()
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-iteration", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-iteration@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_iteration_dto(self, version, index, full_id):
        body = {
            "num": 1,
            "path": "foobar",
            "status": "pass",
        }
        source = {
            "cdm": {"ver": version},
            "iteration": body
            | {
                "iteration-uuid": "foobar",
                "primary-metric": "test::metric",
                "primary-period": "measurement",
            },
        }
        if index:
            source = {"_index": index, "_source": source}
        iter = IterationDTO(source)
        assert iter.version == version
        assert (
            body
            | {
                "id": full_id if full_id else "foobar",
                "uuid": "foobar",
                "primary_metric": "test::metric",
                "primary_period": "measurement",
                "params": {},
            }
            == iter.json()
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-sample", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-sample@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_sample_dto(self, version, index, full_id):
        body = {
            "path": None,
            "status": "pass",
        }
        source = {
            "cdm": {"ver": version},
            "iteration": {
                "iteration-uuid": "one",
                "num": 1,
                "primary-metric": "source::type",
                "primary-period": "measurement",
            },
            "sample": body | {"sample-uuid": "foobar", "num": "1"},
        }
        if index:
            source = {"_index": index, "_source": source}
        sample = SampleDTO(source)
        assert sample.version == version
        assert (
            body
            | {
                "id": full_id if full_id else "foobar",
                "uuid": "foobar",
                "iteration": 1,
                "num": 1,
                "primary_metric": "source::type",
                "primary_period": "measurement",
            }
            == sample.json()
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-period", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-period@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_period_dto(self, version, index, full_id):
        body = {"name": "measurement"}
        source = {
            "cdm": {"ver": version},
            "run": {"run-uuid": "one"},
            "iteration": {
                "iteration-uuid": "one-one",
                "num": 1,
                "primary-period": "measurement",
                "primary-metric": "source::type",
                "status": "pass",
            },
            "sample": {"sample-uuid": "one-one-one", "num": "1"},
            "period": body
            | {
                "period-uuid": "foobar",
                "name": "measurement",
                "begin": "1726162827982",
                "end": "1726164203132",
            },
        }
        if index:
            source = {"_index": index, "_source": source}
        period = PeriodDTO(source)
        assert period.version == version
        assert (
            body
            | {
                "id": full_id if full_id else "foobar",
                "uuid": "foobar",
                "begin": 1726162827982,
                "begin_date": "2024-09-12 17:40:27.982000+00:00",
                "end": 1726164203132,
                "end_date": "2024-09-12 18:03:23.132000+00:00",
                "iteration": 1,
                "sample": "1",
                "name": "measurement",
                "is_primary": True,
                "primary_metric": "source::type",
                "status": "pass",
            }
            == period.json()
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-metric_desc", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-metric_desc@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_metric_dto(self, version, index, full_id):
        body = {
            "class": "throughput",
            "names": {"benchmark-name": "none", "tool-name": "test"},
            "source": "test",
            "type": "metric",
        }
        source = {
            "cdm": {"ver": version},
            "metric_desc": body
            | {
                "metric_desc-uuid": "foobar",
                "names-list": ["benchmark-name", "tool-name"],
            },
        }
        if index:
            source = {"_index": index, "_source": source}
        metric = MetricDTO(source)
        assert metric.version == version
        assert (
            body
            | {
                "id": full_id if full_id else "foobar",
                "uuid": "foobar",
                "names_list": ["benchmark-name", "tool-name"],
            }
            == metric.json()
        )

    @pytest.mark.parametrize(
        "version,index,full_id",
        (
            ("v8dev", None, None),
            ("v8dev", "cdmv8dev-metric_data", "foobar@v8dev@"),
            ("v9dev", None, None),
            ("v9dev", "cdm-v9dev-metric_data@2025.05", "foobar@v9dev@2025.05"),
        ),
    )
    def test_data_dto(self, version, index, full_id):
        body = {}
        source = {
            "cdm": {"ver": version},
            "metric_data": body
            | {
                "begin": "1724702817001",
                "duration": 15000,
                "end": "1724702832000",
                "value": "82.930000",
            },
        }
        if index:
            source = {"_index": index, "_source": source}
        data = DataDTO(source)
        assert data.version == version
        assert (
            body
            | {
                "begin": "2024-08-26 20:06:57.001000+00:00",
                "duration": 15.0,
                "end": "2024-08-26 20:07:12+00:00",
                "value": 82.930000,
            }
            == data.json()
        )


class TestGetIndex:

    async def test_v8_simple(self, fake_crucible):
        """Test a simple CDMv8 date range"""
        idx = await fake_crucible._get_index("run")
        assert idx == "cdmv8dev-run"

    async def test_v8_date(self, fake_crucible):
        """Test with a CDMv8 date range (no effect)"""
        idx = await fake_crucible._get_index("run", "2025-01-01", "2025-03-03")
        assert idx == "cdmv8dev-run"

    @pytest.mark.parametrize("fid", (FullID("abc", "v8dev"), "abc@v8dev"))
    async def test_v8_ref_id(self, fake_crucible, fid):
        """Test locking index with a reference ID, both string and FullID"""
        idx = await fake_crucible._get_index("run", ref_id=fid)
        assert idx == "cdmv8dev-run"

    async def test_v9_simple(self, fake_crucible):
        """Test a simple CDMv9 index"""
        fake_crucible.versions = {"v9dev"}
        idx = await fake_crucible._get_index("run")
        assert idx == "cdm-v9dev-run@*"

    async def test_v9_date(self, fake_crucible):
        """Test an index date range"""
        fake_crucible.versions = {"v9dev"}
        idx = await fake_crucible._get_index("run", "2025-01-01", "2025-03-05")
        assert set(idx.split(",")) == {
            "cdm-v9dev-run@2025.01",
            "cdm-v9dev-run@2025.02",
            "cdm-v9dev-run@2025.03",
        }

    @pytest.mark.parametrize(
        "fid", (FullID("abc", "v9dev", "2025.05"), "abc@v9dev@2025.05")
    )
    async def test_v9_ref_id(self, fake_crucible, fid):
        """Test locking index with a reference ID, both string and FullID"""
        idx = await fake_crucible._get_index("run", ref_id=fid)
        assert idx == "cdm-v9dev-run@2025.05"


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

    def test_raw_hits(self):
        """Test that iteration through "raw" hits works"""

        expected = [{"_source": {"a": 1}}, {"_source": {"b": 1}}]
        assert expected == list(
            CrucibleService._hits({"hits": {"hits": expected}}, raw=True)
        )

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
    def test_build_period_filters(self, fake_crucible: CrucibleService, periods):
        expected = (
            []
            if not periods
            else [
                {
                    "dis_max": {
                        "queries": [
                            {"bool": {"must_not": {"exists": {"field": "period"}}}},
                            {"terms": {"period.period-uuid": periods}},
                        ]
                    }
                }
            ]
        )
        assert expected == fake_crucible._build_period_filters(periods)

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
                            "period-uuid": "one",
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
            plist = [p["period"]["period-uuid"] for p in periods]
        assert result == await fake_crucible._build_timestamp_range_filters(plist)

    @pytest.mark.parametrize(
        "period,name",
        (
            (
                {"period": {"period-uuid": "one"}},
                "run None:None,iteration None,sample None",
            ),
            (
                {
                    "run": {"run-uuid": "rid", "benchmark": "test", "begin": "1234"},
                    "iteration": {"iteration-uuid": "iid", "num": 1},
                    "sample": {"sample-uuid": "sid", "num": 1},
                    "period": {"period-uuid": "one", "begin": "5423"},
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
            "Cannot process metric time filter: at least one of "
            "the periods in 'one' is broken and lacks a time range." == exc.value.detail
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
            filters=[{"term": "a"}],
            aggregations=[{"x": {"field": "a"}}],
            sort=[{"key": "asc"}],
            source="run",
            size=42,
            offset=69,
            x=2,
            z=3,
        )
        assert [
            Request(
                "cdmv8dev-run",
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
        result = await fake_crucible._get_metric_ids("runid", "source::type")
        assert result == []

    @pytest.mark.parametrize(
        "found,expected,aggregate",
        (
            (
                [
                    {"metric_desc": {"metric_desc-uuid": "one-metric"}},
                ],
                ["one-metric"],
                False,
            ),
            (
                [
                    {"metric_desc": {"metric_desc-uuid": "one-metric"}},
                ],
                ["one-metric"],
                True,
            ),
            (
                [
                    {"metric_desc": {"metric_desc-uuid": "one-metric"}},
                    {"metric_desc": {"metric_desc-uuid": "two-metric"}},
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
                    {
                        "metric_desc": {
                            "metric_desc-uuid": "one-metric",
                            "names": {"john": "yes"},
                        }
                    },
                    {
                        "metric_desc": {
                            "metric_desc-uuid": "two-metric",
                            "names": {"john": "no"},
                        }
                    },
                ],
                (2, [], {"john": ["no", "yes"]}),
            ),
            (
                [
                    {
                        "period": {"period-uuid": "p1"},
                        "metric_desc": {
                            "metric_desc-uuid": "three-metric",
                            "names": {"john": "yes"},
                        },
                    },
                    {
                        "metric_desc": {
                            "metric_desc-uuid": "four-metric",
                            "names": {"fred": "why"},
                        }
                    },
                    {
                        "period": {"period-uuid": "p2"},
                        "metric_desc": {
                            "metric_desc-uuid": "five-metric",
                            "names": {"john": "sure"},
                        },
                    },
                    {
                        "metric_desc": {
                            "metric_desc-uuid": "six-metric",
                            "names": {"john": "maybe"},
                        }
                    },
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
            [
                {"run": {"run-uuid": "one"}},
                {"run": {"run-uuid": "two"}},
                {"run": {"run-uuid": "three"}},
            ],
        )
        assert {"one", "two", "three"} == await fake_crucible._get_run_ids(
            "period", [{"term": {"period.name": "measurement"}}]
        )

    async def test_get_runs_none(self, fake_crucible: CrucibleService):
        """Test run summary"""
        fake_crucible.elastic.set_query("run", [])
        fake_crucible.elastic.set_query("iteration", [])
        fake_crucible.elastic.set_query("period", [])
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
        fake_crucible.elastic.set_query("period", [])
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
    @pytest.mark.parametrize(
        "begin,end", (("0", "5000"), (None, None), ("0", None), (None, "5000"))
    )
    async def test_get_runs_queries(
        self, args, miss, notag, noparam, begin, end, fake_crucible: CrucibleService
    ):
        """Test processing of various query parameters

        Note, this isn't really testing "behavior" of the filters, which is all
        in Opensearch, just the CPT service's handling of the query parameters.

        TBD: This should really verify the generated Opensearch query filters,
        although that's mostly covered by earlier tests.
        """
        runs = [
            {
                "run": {
                    "run-uuid": "r1",
                    "begin": begin,
                    "end": end,
                    "benchmark": "test",
                }
            },
        ]
        if miss:
            # Add additional runs which will be rejected by filters
            runs.extend(
                [
                    {
                        "run": {
                            "run-uuid": "r2",
                            "begin": "110",
                            "end": "7000",
                            "benchmark": "test",
                            "source": "abc",
                        }
                    },
                    {
                        "run": {
                            "run-uuid": "r3",
                            "begin": "110",
                            "end": "6000",
                            "benchmark": "test",
                            "email": "a@b.c",
                        }
                    },
                ]
            )
        fake_crucible.elastic.set_query("run", runs)
        fake_crucible.elastic.set_query(
            "iteration",
            [
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {
                        "iteration-uuid": "r1-i1",
                        "num": 1,
                        "primary-period": "tp",
                        "primary-metric": "src::tst1",
                        "status": "pass",
                    },
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {
                        "iteration-uuid": "r1-i2",
                        "num": 2,
                        "primary-period": "tp",
                        "primary-metric": "src::tst2",
                        "status": "pass",
                    },
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {
                        "iteration-uuid": "r1-i3",
                        "num": 3,
                        "primary-period": "tp",
                        "primary-metric": "src::tst1",
                        "status": "fail",
                    },
                },
            ],
        )
        fake_crucible.elastic.set_query(
            "period",
            [
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {
                        "iteration-uuid": "r1-i1",
                        "num": 1,
                        "path": None,
                        "primary-metric": "test::metric",
                        "primary-period": "p1",
                        "status": "pass",
                    },
                    "sample": {
                        "num": 2,
                        "path": None,
                        "status": "pass",
                        "sample-uuid": "r1-s1",
                    },
                    "period": {
                        "period-uuid": "r1-p1",
                        "begin": 0,
                        "end": 100,
                        "name": "default",
                    },
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {
                        "iteration-uuid": "r1-i2",
                        "num": 2,
                        "path": None,
                        "primary-metric": "test::metric",
                        "primary-period": "p1",
                        "status": "pass",
                    },
                    "sample": {
                        "num": 1,
                        "path": None,
                        "status": "pass",
                        "sample-uuid": "r1-s2",
                    },
                    "period": {
                        "period-uuid": "r1-p2",
                        "begin": 100,
                        "end": 5000,
                        "name": "default",
                    },
                },
            ],
        )

        if notag:
            tags = []
        else:
            tags = [
                {"run": {"run-uuid": "r1"}, "tag": {"name": "a", "val": 42}},
                {"run": {"run-uuid": "r2"}, "tag": {"name": "a", "val": 42}},
            ]
        fake_crucible.elastic.set_query("tag", tags, repeat=2)

        if noparam:
            params = []
        else:
            params = [
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "r1-i1"},
                    "param": {"arg": "b", "val": "cde"},
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "r1-i1"},
                    "param": {"arg": "z", "val": "xyzzy"},
                },
                {
                    "run": {"run-uuid": "r3"},
                    "iteration": {"iteration-uuid": "r3-i1"},
                    "param": {"arg": "z", "val": "xyzzy"},
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "r1-i2"},
                    "param": {"arg": "b", "val": "cde"},
                },
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "r1-i2"},
                    "param": {"arg": "x", "val": "plugh"},
                },
            ]
        fake_crucible.elastic.set_query("param", params, repeat=2)
        expected = {
            "count": 1,
            "offset": 0,
            "results": [
                {
                    "id": "r1@v8dev@",
                    "uuid": "r1",
                    "begin": 0,
                    "begin_date": "1970-01-01 00:00:00+00:00",
                    "benchmark": "test",
                    "end": 5000,
                    "end_date": "1970-01-01 00:00:05+00:00",
                    "name": None,
                    "source": None,
                    "email": None,
                    "host": None,
                    "harness": None,
                    "iterations": [
                        {
                            "id": "r1-i1@v8dev@",
                            "uuid": "r1-i1",
                            "num": 1,
                            "params": (
                                {}
                                if noparam
                                else {
                                    "b": "cde",
                                    "z": "xyzzy",
                                }
                            ),
                            "path": None,
                            "primary_metric": "src::tst1",
                            "primary_period": "tp",
                            "status": "pass",
                        },
                        {
                            "id": "r1-i2@v8dev@",
                            "uuid": "r1-i2",
                            "num": 2,
                            "params": (
                                {}
                                if noparam
                                else {
                                    "b": "cde",
                                    "x": "plugh",
                                }
                            ),
                            "path": None,
                            "primary_metric": "src::tst2",
                            "primary_period": "tp",
                            "status": "pass",
                        },
                        {
                            "id": "r1-i3@v8dev@",
                            "uuid": "r1-i3",
                            "num": 3,
                            "params": {},
                            "path": None,
                            "primary_metric": "src::tst1",
                            "primary_period": "tp",
                            "status": "fail",
                        },
                    ],
                    "params": {},
                    "primary_metrics": ["src::tst1", "src::tst2"],
                    "status": "fail",
                    "tags": {"a": 42},
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
                {"run": {"run-uuid": "one"}, "tag": {"name": "a", "val": 123}},
                {"run": {"run-uuid": "one"}, "tag": {"name": "b", "val": "hello"}},
                {"run": {"run-uuid": "one"}, "tag": {"name": "c", "val": False}},
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
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "b", "val": 5},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "c", "val": "val"},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid2"},
                "param": {"arg": "a", "val": 7},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid2"},
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
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "b", "val": 5},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
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
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "a", "val": 10},
            },
            {
                "run": {"run-uuid": "rid"},
                "iteration": {"iteration-uuid": "iid1"},
                "param": {"arg": "a", "val": 5},
            },
        ]
        fake_crucible.elastic.set_query("param", params)
        assert {"iid1": {"a": 5}} == await fake_crucible.get_params(None, "iid1")

    async def test_get_iterations(self, fake_crucible: CrucibleService):
        """Get iterations for a run ID"""
        iterations = [
            {
                "id": "one@v8dev@",
                "uuid": "one",
                "num": 1,
                "path": None,
                "params": {},
                "primary_metric": "test::metric1",
                "primary_period": "measurement",
                "status": "pass",
            },
            {
                "id": "two@v8dev@",
                "uuid": "two",
                "num": 2,
                "path": None,
                "params": {},
                "primary_metric": "test::metric2",
                "primary_period": "measurement",
                "status": "pass",
            },
            {
                "id": "three@v8dev@",
                "uuid": "three",
                "num": 3,
                "path": None,
                "params": {},
                "primary_metric": "test::metric1",
                "primary_period": "measurement",
                "status": "pass",
            },
        ]
        fake_crucible.elastic.set_query(
            "iteration",
            [
                {
                    "run": {"run-uuid": "one"},
                    "iteration": {
                        "iteration-uuid" if k == "uuid" else k.replace("_", "-"): v
                        for k, v in i.items()
                    },
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

    @pytest.mark.parametrize("ids", (("one", None), (None, "one-one")))
    async def test_get_samples(self, fake_crucible: CrucibleService, ids):
        """Get samples for a run ID"""
        samples = [
            {
                "id": "one@v8dev@",
                "uuid": "one",
                "num": 1,
                "path": None,
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
            {
                "id": "two@v8dev@",
                "uuid": "two",
                "num": 2,
                "path": None,
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
            {
                "id": "three@v8dev@",
                "uuid": "three",
                "num": 3,
                "path": None,
                "status": "pass",
                "primary_metric": "pm",
                "primary_period": "m",
                "iteration": 1,
            },
        ]
        raw_samples = [
            {"sample-uuid": "one", "num": "1", "path": None, "status": "pass"},
            {"sample-uuid": "two", "num": "2", "path": None, "status": "pass"},
            {"sample-uuid": "three", "num": "3", "path": None, "status": "pass"},
        ]
        fake_crucible.elastic.set_query(
            "sample",
            [
                {
                    "run": {"run-uuid": "one"},
                    "iteration": {
                        "iteration-uuid": "one-one",
                        "primary-metric": "pm",
                        "primary-period": "m",
                        "num": 1,
                        "status": "pass",
                    },
                    "sample": s,
                }
                for s in raw_samples
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
        "ids",
        (("one", None, None), (None, "one-one", None), (None, None, "one-one-one")),
    )
    async def test_get_periods(self, fake_crucible: CrucibleService, ids):
        """Get samples for a run ID"""
        periods = [
            {
                "begin": 1733433391046,
                "end": 1733434831166,
                "begin_date": "2024-12-05 21:16:31.046000+00:00",
                "end_date": "2024-12-05 21:40:31.166000+00:00",
                "id": "306C8A78-B352-11EF-8E37-AD212D0A0B9F@v8dev@",
                "uuid": "306C8A78-B352-11EF-8E37-AD212D0A0B9F",
                "name": "measurement",
                "is_primary": True,
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
                    "run": {"run-uuid": "one"},
                    "iteration": {
                        "iteration-uuid": "one-one",
                        "primary-metric": None,
                        "primary-period": "measurement",
                        "num": 1,
                        "status": p["status"],
                    },
                    "sample": {
                        "sample-uuid": "one-one-one",
                        "num": 1,
                        "status": p["status"],
                        "path": None,
                    },
                    "period": {
                        "period-uuid": p["uuid"],
                        "name": p["name"],
                        "begin": p["begin"],
                        "end": p["end"],
                        "primary-metric": p["primary_metric"],
                        "status": p["status"],
                    },
                }
                for p in periods
            ],
        )
        fake_crucible.elastic.set_query(
            "iteration",
            [
                {
                    "run": {"run-uuid": "one"},
                    "iteration": {
                        "iteration-uuid": "one-one",
                        "primary-metric": p["primary_metric"],
                        "primary-period": "measurement",
                        "num": 1,
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
                "run": {"run-uuid": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"run-uuid": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"run-uuid": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value2"},
                },
            },
            {
                "run": {"run-uuid": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "names": {"name1": "value2"},
                },
            },
            {
                "run": {"run-uuid": "one"},
                "period": {"period-uuid": "p1"},
                "metric_desc": {"source": "source1", "type": "type2", "names": {}},
            },
            {
                "run": {"run-uuid": "one"},
                "period": {"period-uuid": "p2"},
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
            "run": {"run-uuid": "one"},
            "metric_desc": {
                "source": "source1",
                "type": "type1",
                "class": "classy",
                "names": {"name1": "value1"},
            },
        }
        md2 = {
            "run": {"run-uuid": "one"},
            "metric_desc": {
                "source": "source1",
                "type": "type1",
                "names": {"name1": "value2"},
            },
        }
        if period:
            metrics["periods"] = ["p1", "p2"]
            md1["period"] = {"period-uuid": "p1"}
            md2["period"] = {"period-uuid": "p2"}
        query = [
            md1,
            md2,
            {
                "run": {"run-uuid": "one"},
                "metric_desc": {
                    "source": "source1",
                    "type": "type1",
                    "class": "classless",
                    "names": {"name1": "value1"},
                },
            },
            {
                "run": {"run-uuid": "one"},
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
            [{"metric_desc": {"metric_desc-uuid": "one-metric", "names": {}}}],
        )
        fake_crucible.elastic.set_query(
            "metric_data",
            [
                {
                    "metric_desc": {"metric_desc-uuid": "one-metric"},
                    "metric_data": {
                        "begin": "1726165775123",
                        "end": "1726165789213",
                        "duration": 14100,
                        "value": 9.35271216694379,
                    },
                },
                {
                    "metric_desc": {"metric_desc-uuid": "one-metric"},
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
                "cdmv8dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "runid",
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
                "cdmv8dev-metric_data",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.metric_desc-uuid": [
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
                {"metric_desc": {"metric_desc-uuid": "one-metric", "names": {}}},
                {"metric_desc": {"metric_desc-uuid": "two-metric", "names": {}}},
            ],
        )
        fake_crucible.elastic.set_query(
            "metric_data",
            aggregations={"duration": {"value": 14022}},
        )
        if count:
            intervals = [
                {"key": 1726165789213, "value": {"value": 9.35271216694379}},
                {"key": 1726165804022, "value": {"value": 9.405932330557683}},
            ]
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
            intervals = []
            expected = []
        fake_crucible.elastic.set_query(
            "metric_data",
            aggregations={"interval": intervals},
        )
        assert expected == await fake_crucible.get_metrics_data(
            "r1", "source::type", aggregate=True
        )
        expected_requests = [
            Request(
                "cdmv8dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "r1",
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
                "cdmv8dev-metric_data",
                {
                    "aggs": {
                        "duration": {
                            "min": {
                                "field": "metric_data.duration",
                            },
                        },
                    },
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.metric_desc-uuid": [
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
                "cdmv8dev-metric_data",
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
                                        "metric_desc.metric_desc-uuid": [
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
        assert fake_crucible.elastic.requests == expected_requests

    async def test_metrics_summary(self, fake_crucible: CrucibleService):
        """Return data summary for a fully-qualified metric"""

        fake_crucible.elastic.set_query(
            "metric_desc",
            [
                {
                    "metric_desc": {
                        "metric_desc-uuid": "one-metric",
                        "names": {"a": "1"},
                    }
                },
            ],
        )
        expected = [
            {
                "aggregate": False,
                "title": "ABC",
                "periods": None,
                "metric": "one-metric::type",
                "names": ["a=1"],
                "run": "runid",
                "count": 5,
                "min": 9.35271216694379,
                "max": 9.405932330557683,
                "avg": 9.379322249,
                "sum": 18.758644498,
            }
        ]
        fake_crucible.elastic.set_query(
            "metric_data",
            aggregations={
                "score": {
                    "count": 5,
                    "min": 9.35271216694379,
                    "max": 9.405932330557683,
                    "avg": 9.379322249,
                    "sum": 18.758644498,
                }
            },
        )
        assert expected == await fake_crucible.get_metrics_summary(
            [Metric(run="runid", metric="one-metric::type", names=["a=1"], title="ABC")]
        )
        assert fake_crucible.elastic.requests == [
            Request(
                "cdmv8dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "runid",
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
                "cdmv8dev-metric_data",
                {
                    "aggs": {
                        "score": {"extended_stats": {"field": "metric_data.value"}}
                    },
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "terms": {
                                        "metric_desc.metric_desc-uuid": [
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
            ([], 0, ["p1"], 0, "source::type dave (n=42)"),
            ([], 1, ["p1"], 1, "source::type alyssa"),
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
            {
                "r1": {
                    "i1": [{"period-uuid": "p1", "name": "dave"}],
                    "i2": [{"period-uuid": "p2", "name": "amy"}],
                }
            },
            {"r1": {"i1": [{"period-uuid": "p1", "name": "alyssa"}]}},
            {"r1": {"i1": [{"period-uuid": "p2", "name": "ken"}]}},
        ][period_idx]
        name = await fake_crucible._make_title(
            "r1",
            runs,
            Metric(run="r1", metric="source::type", periods=periods),
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
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "i1"},
                    "param": {"arg": "a", "val": "1"},
                },
            ],
        )
        fake_crucible.elastic.set_query(
            "period",
            [
                {
                    "run": {"run-uuid": "r1"},
                    "iteration": {"iteration-uuid": "i1"},
                    "period": {"period-uuid": "p1", "name": "alan"},
                },
            ],
        )
        name = await fake_crucible._make_title(
            "r1",
            [],
            Metric(run="r1", metric="source::type"),
            param_runs,
            period_runs,
        )
        assert name == "source::type"
        assert fake_crucible.elastic.requests == [
            Request(
                "cdmv8dev-param",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "r1",
                                    },
                                },
                            ],
                        },
                    },
                    "size": 262144,
                },
            ),
            Request(
                "cdmv8dev-period",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "r1",
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
                    graphs=[
                        Metric(
                            run="",
                            metric="source::type",
                            aggregate=True,
                            title="test",
                        )
                    ],
                )
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == "each graph request must have a run ID"

    @pytest.mark.parametrize("count", (0, 2))
    async def test_metrics_graph(self, count, fake_crucible: CrucibleService):
        """Return graph for aggregated metrics"""

        metrics = [{"metric_desc": {"metric_desc-uuid": "one-metric", "names": {}}}]
        if count:
            metrics.append(
                {"metric_desc": {"metric_desc-uuid": "two-metric", "names": {}}}
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
                    "autosize": True,
                    "legend": {
                        "groupclick": "toggleitem",
                        "orientation": "h",
                        "x": 0.9,
                        "xanchor": "right",
                        "xref": "container",
                        "y": 1,
                        "yanchor": "top",
                        "yref": "container",
                    },
                    "responsive": True,
                    "showlegend": True,
                    "xaxis": {
                        "tickformat": "%Y:%M:%d %X %Z",
                        "title": {
                            "font": {
                                "color": "gray",
                                "variant": "petite-caps",
                                "weight": 1000,
                            },
                            "text": "sample timestamp",
                        },
                        "type": "date",
                    },
                    "xaxis_title": "sample timestamp",
                    "yaxis_title": "Metric value",
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
                    "autosize": True,
                    "legend": {
                        "groupclick": "toggleitem",
                        "orientation": "h",
                        "x": 0.9,
                        "xanchor": "right",
                        "xref": "container",
                        "y": 1,
                        "yanchor": "top",
                        "yref": "container",
                    },
                    "responsive": True,
                    "showlegend": True,
                    "xaxis": {
                        "tickformat": "%Y:%M:%d %X %Z",
                        "title": {
                            "font": {
                                "color": "gray",
                                "variant": "petite-caps",
                                "weight": 1000,
                            },
                            "text": "sample timestamp",
                        },
                        "type": "date",
                    },
                    "xaxis_title": "sample timestamp",
                    "yaxis_title": "Metric value",
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
                name="graph",
                graphs=[
                    Metric(
                        run="r1", metric="source::type", aggregate=True, title="test"
                    )
                ],
            )
        )
        expected_requests = [
            Request(
                "cdmv8dev-metric_desc",
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "run.run-uuid": "r1",
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
                        "cdmv8dev-metric_data",
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
                                                "metric_desc.metric_desc-uuid": [
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
                        "cdmv8dev-metric_data",
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
                                                "metric_desc.metric_desc-uuid": [
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
                    "cdmv8dev-metric_data",
                    {
                        "query": {
                            "bool": {
                                "filter": [
                                    {
                                        "terms": {
                                            "metric_desc.metric_desc-uuid": [
                                                "one-metric"
                                            ],
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
