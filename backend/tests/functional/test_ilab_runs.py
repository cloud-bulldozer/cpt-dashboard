from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
import requests


@dataclass
class Run:
    id: str
    start: int
    metrics: list[str]
    iterations: int


# The "annointed" functional test Opensearch contains 5 ilab benchmark results.
# These are in (begin) timestamp order for comparison purposes.
RUNS: list[Run] = [
    Run(
        "26ad48c1-fc9c-404d-bccf-d19755ca8a39",
        1726165775123,
        ["ilab::sdg-samples-sec"],
        5,
    ),
    Run(
        "1878b7d2-9195-4104-8bd0-13d31a8f5524",
        1730136441057,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "1c756d89-3aef-445b-b71b-99b8916f8537",
        1730212256723,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "20a15c35-22ac-482f-b209-4b8ecc018a26",
        1732201767072,
        ["ilab::actual-train-seconds", "ilab::sdg-samples-sec"],
        2,
    ),
    Run(
        "0d78ece9-817c-41aa-be19-e90d53924206",
        1732208487941,
        ["ilab::actual-train-seconds", "ilab::sdg-samples-sec"],
        2,
    ),
]


class TestIlabRuns:

    def test_get_runs(self, server):

        # Get all runs, regardless of date
        response = requests.get(f"{server}/api/v1/ilab/runs", params={"all": "true"})
        assert response.status_code == 200
        result = response.json()

        # Our test database has 5 runs
        assert result["total"] == 5

        # We should get the expected run IDs
        assert {r["id"] for r in result["results"]} == {e.id for e in RUNS}

        # All runs in the test database are from the "ilab" benchmark
        assert {r["benchmark"] for r in result["results"]} == {"ilab"}

        # All Crucible runs "passed"
        assert {r["status"] for r in result["results"]} == {"pass"}

    @pytest.mark.parametrize("start,end", ((None, 2), (2, None), (2, 4)))
    def test_date_filter(self, server, start, end):
        """Test that date filters work"""
        sdate = None
        edate = None
        first = 0
        last = 5

        if start:
            first = start
            stime = datetime.fromtimestamp(RUNS[start].start / 1000, timezone.utc)
            sdate = f"{stime:%Y-%m-%dT%H:%M:%S}"
        if end:
            last = end
            etime = datetime.fromtimestamp(RUNS[end].start / 1000, tz=timezone.utc)
            edate = f"{etime:%Y-%m-%dT%H:%M:%S}"
        response = requests.get(
            f"{server}/api/v1/ilab/runs", {"start_date": sdate, "end_date": edate}
        )
        result = response.json()
        ids = {r.id for r in RUNS[first:last]}
        assert result["total"] == len(ids)
        assert {r["id"] for r in result["results"]} == ids

    def test_pagination(self, server):
        response = requests.get(
            f"{server}/api/v1/ilab/runs", {"all": "true", "size": 3, "offset": 1}
        )
        result = response.json()
        assert result["total"] == 5
        assert result["count"] == 3
        assert {r["id"] for r in result["results"]} == {
            RUNS[1].id,
            RUNS[2].id,
            RUNS[3].id,
        }
        assert result["next_offset"] == 4

        response = requests.get(
            f"{server}/api/v1/ilab/runs",
            {"all": "true", "size": 3, "offset": result["next_offset"]},
        )
        result = response.json()
        assert result["total"] == 5
        assert result["count"] == 1
        assert result["results"][0]["id"] == RUNS[4].id
        assert "next_offset" not in result
