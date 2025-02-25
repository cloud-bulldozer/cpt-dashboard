from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
import pytest
from vyper import Vyper

import app.config
from app.services.crucible_svc import CommonParams, CrucibleService, Parser
from tests.fake_elastic import FakeAsyncElasticsearch


@pytest.fixture
def fake_config(monkeypatch):
    """Provide a fake configuration"""

    vyper = Vyper(config_name="ocpperf")
    vyper.set("TEST.url", "http://elastic.example.com:9200")
    monkeypatch.setattr("app.config.get_config", lambda: vyper)


@pytest.fixture
def fake_elastic(monkeypatch, fake_config):
    """Replace the actual elastic client with a fake"""

    monkeypatch.setattr(
        "app.services.crucible_svc.AsyncElasticsearch", FakeAsyncElasticsearch
    )


@pytest.fixture
async def fake_crucible(fake_elastic):
    crucible = CrucibleService("TEST")
    yield crucible
    await crucible.close()


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
            assert f"Unexpected result {type(a)}"

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

    async def test_metric_ids_none(self, fake_crucible):
        """A simple query for failure matching metric IDs"""

        fake_crucible.elastic.set_query("metric_desc", [])
        with pytest.raises(HTTPException) as e:
            await fake_crucible._get_metric_ids("runid", "source::type")
        assert 400 == e.value.status_code
        assert "No matches for source::type" == e.value.detail

    @pytest.mark.parametrize(
        "found,expected",
        (
            (
                [
                    {"metric_desc": {"id": "one-metric"}},
                ],
                ["one-metric"],
            ),
            (
                [
                    {"metric_desc": {"id": "one-metric"}},
                    {"metric_desc": {"id": "two-metric"}},
                ],
                ["one-metric", "two-metric"],
            ),
        ),
    )
    async def test_metric_ids(self, fake_crucible, found, expected):
        """A simple query for matching metric IDs"""

        fake_crucible.elastic.set_query("metric_desc", found)
        assert expected == await fake_crucible._get_metric_ids(
            "runid",
            "source::type",
            aggregate=len(expected) > 1,
        )

    async def test_run_filters(self, fake_crucible):
        """Test aggregations

        This is the "simplest" aggregation-based query, but we need to define
        fake aggregations for the tag, param, and run indices.
        """

        fake_crucible.elastic.set_query(
            "tag",
            aggregation_list={
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
            aggregation_list={
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
            aggregation_list={
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
