from datetime import datetime

from fastapi import HTTPException
import pytest
from starlette.testclient import TestClient

from app.main import app as fastapi_app
from app.services.crucible_svc import CrucibleService, Graph, GraphList


@pytest.fixture
def client():
    """Create a Starlette test client."""
    yield TestClient(fastapi_app)


class TestInit:

    @pytest.mark.parametrize(
        "exc", (None, HTTPException(status_code=501, detail="test"))
    )
    def test_crucible(self, exc, monkeypatch, client: TestClient):

        class FakeCrucible(CrucibleService):
            def __init__(self, config):
                if exc:
                    raise exc
                self.url = "For me to know"

            async def get_run_filters(self) -> dict[str, list[str]]:
                return {}

            async def close(self):
                pass

        monkeypatch.setattr(
            "app.api.v1.endpoints.ilab.ilab.CrucibleService", FakeCrucible
        )
        response = client.get("/api/v1/ilab/runs/filters")
        if exc:
            assert response.json() == {"detail": "test"}
            assert response.status_code == 501
        else:
            assert response.json() == {}
            assert response.status_code == 200


class TestIlabApi:

    def test_filters(self, monkeypatch, client: TestClient, fake_crucible):
        async def fake_get(self):
            return {"param": {}, "tag": {}, "run": {}}

        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_run_filters", fake_get
        )
        response = client.get("/api/v1/ilab/runs/filters")
        assert response.json() == {"param": {}, "tag": {}, "run": {}}
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "stime,etime,expected_start,expected_end",
        (
            (None, None, "2023-12-16T10:05:00.000100", "2024-01-15T10:05:00.000100"),
            ("2024-01-01", None, "2024-01-01", None),
            (None, "2024-02-01", None, "2024-02-01"),
            ("2024-01-01", "2024-02-01", "2024-01-01", "2024-02-01"),
        ),
    )
    def test_runs(
        self,
        stime,
        etime,
        expected_start,
        expected_end,
        monkeypatch,
        client: TestClient,
        fake_crucible,
    ):
        expected = {
            "results": [],
            "count": 0,
            "total": 0,
            "startDate": expected_start,
            "endDate": expected_end,
        }
        not_now = datetime(2024, 1, 15, 10, 5, 0, 100)

        class mydatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return not_now

        async def fake_get(self, start, end, filter, sort, size, offset):
            return {
                "results": [],
                "count": 0,
                "total": 0,
                "startDate": (
                    start.isoformat() if isinstance(start, datetime) else start
                ),
                "endDate": end.isoformat() if isinstance(end, datetime) else end,
            }

        monkeypatch.setattr("app.api.v1.endpoints.ilab.ilab.datetime", mydatetime)
        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_runs", fake_get
        )
        queries = {}
        if stime:
            queries["start_date"] = stime
        if etime:
            queries["end_date"] = etime
        response = client.get("/api/v1/ilab/runs", params=queries)
        assert response.json() == expected
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "api,name,detail",
        (
            ("tags", "get_tags", {"tag": "value"}),
            ("params", "get_params", {"i1": {"key": 1}}),
            ("iterations", "get_iterations", [{"i1": {"num": 1}}]),
            ("samples", "get_samples", [{"num": "1"}]),
            ("periods", "get_periods", [{"name": "period"}]),
            (
                "metrics",
                "get_metrics_list",
                {"source::type": {"periods": [], "breakouts": {}}},
            ),
        ),
    )
    def test_run_detail(
        self, api, name, detail, monkeypatch, client: TestClient, fake_crucible
    ):
        async def fake_get(self, run):
            assert run == "r1"
            return detail

        monkeypatch.setattr(
            f"app.services.crucible_svc.CrucibleService.{name}", fake_get
        )
        response = client.get(f"/api/v1/ilab/runs/r1/{api}")
        assert response.json() == detail
        assert response.status_code == 200

    def test_iteration_samples(self, monkeypatch, client: TestClient, fake_crucible):
        async def fake_get(self, run=None, iteration=None):
            assert run is None
            assert iteration == "i1"
            return [{"num": "2"}]

        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_samples", fake_get
        )
        response = client.get("/api/v1/ilab/iterations/i1/samples")
        assert response.json() == [{"num": "2"}]
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "name,period", ((None, None), (["cpu=1", "x=y"], None), (None, ["p1,p2"]))
    )
    @pytest.mark.parametrize(
        "api,getter",
        (("breakouts", "get_metric_breakouts"), ("summary", "get_metrics_summary")),
    )
    def test_metric_name_period(
        self, name, period, api, getter, monkeypatch, client: TestClient, fake_crucible
    ):
        if api == "breakouts":
            expected = {
                "label": "source::type",
                "class": ["test"],
                "type": "type",
                "source": "source",
                "breakouts": {"one": [1, 2]},
            }
        else:
            expected = {"count": 2, "min": 0.0, "max": 10.0, "avg": 5.0, "sum": 10.0}

        async def fake_get(self, run, metric, names, periods):
            assert run == "r1"
            assert metric == "source::type"
            assert names == name
            assert periods == period
            return expected

        monkeypatch.setattr(
            f"app.services.crucible_svc.CrucibleService.{getter}", fake_get
        )
        query = None
        if name or period:
            query = {}
            if name:
                query["name"] = name
            if period:
                query["period"] = period
        response = client.get(f"/api/v1/ilab/runs/r1/{api}/source::type", params=query)
        assert response.json() == expected
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "name,period,agg",
        (
            (None, None, False),
            (["cpu=1", "x=y"], None, False),
            (None, ["p1,p2"], False),
            (["cpu=1", "x=y"], None, True),
            (None, ["p1,p2"], True),
        ),
    )
    def test_metric_data(
        self, name, period, agg, monkeypatch, client: TestClient, fake_crucible
    ):
        expected = [{"begin": "t1", "end": "t2", "duration": 0.0, "value": 0.0}]

        async def fake_get(self, run, metric, names, periods, aggregate):
            assert run == "r1"
            assert metric == "source::type"
            assert names == name
            assert periods == period
            assert aggregate == agg
            return expected

        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_metrics_data", fake_get
        )
        query = None
        if name or period or agg:
            query = {}
            if name:
                query["name"] = name
            if period:
                query["period"] = period
            if agg:
                query["aggregate"] = agg
        response = client.get("/api/v1/ilab/runs/r1/data/source::type", params=query)
        assert response.json() == expected
        assert response.status_code == 200

    def test_multigraph(self, monkeypatch, client: TestClient, fake_crucible):
        expected = [{"data": [{"x": [], "y": []}]}]

        async def fake_get(self, graphs):
            assert graphs == GraphList(
                run="r1", name="graphs", graphs=[Graph(metric="source::type")]
            )
            return expected

        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_metrics_graph", fake_get
        )
        response = client.post(
            "/api/v1/ilab/runs/multigraph",
            json={
                "run": "r1",
                "name": "graphs",
                "graphs": [{"metric": "source::type"}],
            },
        )
        assert response.json() == expected
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "name,period,agg,title",
        (
            (None, None, False, None),
            (["cpu=1", "x=y"], None, False, "title"),
            (None, ["p1,p2"], False, None),
            (["cpu=1", "x=y"], None, True, "t2"),
            (None, ["p1,p2"], True, None),
        ),
    )
    def test_metric_graph(
        self, name, period, agg, title, monkeypatch, client: TestClient, fake_crucible
    ):
        expected = [{"data": [{"x": [], "y": []}]}]

        async def fake_get(self, graphs):
            assert graphs == GraphList(
                run="r1",
                name="source::type",
                graphs=[
                    Graph(
                        metric="source::type",
                        aggregate=agg,
                        names=name,
                        periods=period,
                        title=title,
                    )
                ],
            )
            return expected

        monkeypatch.setattr(
            "app.services.crucible_svc.CrucibleService.get_metrics_graph", fake_get
        )
        query = None
        if name or period or agg or title:
            query = {}
            if name:
                query["name"] = name
            if period:
                query["period"] = period
            if agg:
                query["aggregate"] = agg
            if title:
                query["title"] = title
        response = client.get("/api/v1/ilab/runs/r1/graph/source::type", params=query)
        assert response.json() == expected
        assert response.status_code == 200
