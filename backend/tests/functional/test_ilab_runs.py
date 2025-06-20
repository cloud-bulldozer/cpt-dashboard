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


# The "annointed" functional test Opensearch contains 21 ilab benchmark results.
# These are in (begin) timestamp order for comparison purposes.
RUNS: list[Run] = [
    Run(
        "c8c30b5c-8da4-4354-a33c-75db39f33df2@v9dev@2024.08",
        1724702857739,
        ["ilab::train-samples-sec"],
        1,
    ),
    Run(
        "872548fd-58f0-4b02-a84c-c283002de99f@v9dev@2024.08",
        1724764492612,
        ["ilab::train-samples-sec"],
        1,
    ),
    Run(
        "d2f7c3e6-0610-4571-92aa-9b06aab50403@v9dev@2024.08",
        1724771378865,
        ["ilab::train-samples-sec"],
        1,
    ),
    Run(
        "bd72561c-cc20-400b-b6f6-d9534a60033a@v9dev@2024.09",
        1726084021432,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "824471bb-3a0a-4b0b-99cd-57d2b65985b2@v9dev@2024.09",
        1726090660121,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "e3359d95-fc32-481f-b2e9-6fa402167a2b@v9dev@2024.09",
        1726151194178,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "26ad48c1-fc9c-404d-bccf-d19755ca8a39@v8dev@",
        1726165775123,
        ["ilab::sdg-samples-sec"],
        5,
    ),
    Run(
        "b174e475-0c42-45e8-afe9-f0ebf183c593@v9dev@2024.10",
        1728485267544,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "7e99f36c-b7e1-4bee-9e1d-e67faf3a8136@v9dev@2024.10",
        1729879606324,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "83b6b895-9205-4c74-8697-95bbd2b266e7@v9dev@2024.10",
        1730127499016,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "1878b7d2-9195-4104-8bd0-13d31a8f5524@v8dev@",
        1730136441057,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "1c756d89-3aef-445b-b71b-99b8916f8537@v8dev@",
        1730212256723,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "e20ffce2-a57d-4bbf-800f-0eabb304f452@v8dev@",
        1730983583136,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "2fb71391-3913-4e13-8f84-fbcf56e9375a@v8dev@",
        1731337345207,
        ["ilab::sdg-samples-sec"],
        1,
    ),
    Run(
        "20a15c35-22ac-482f-b209-4b8ecc018a26@v8dev@",
        1732201767072,
        ["ilab::actual-train-seconds", "ilab::sdg-samples-sec"],
        2,
    ),
    Run(
        "0d78ece9-817c-41aa-be19-e90d53924206@v8dev@",
        1732208487941,
        ["ilab::actual-train-seconds", "ilab::sdg-samples-sec"],
        2,
    ),
    Run(
        "04a13827-d975-4424-803a-a7f810d909c9@v8dev@",
        1739830872666,
        ["ilab::actual-train-seconds"],
        3,
    ),
    Run(
        "287bbe71-484b-4673-ab23-3cc4faffb513@v8dev@",
        1740503368827,
        ["ilab::actual-train-seconds"],
        3,
    ),
    Run(
        "ec4afec8-f68b-4724-a534-dbf6fc7a1099@v8dev@",
        1747337948965,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "3c3a67ef-6fdb-4451-9bdc-c58f8bfb712d@v8dev@",
        1747447721946,
        ["ilab::actual-train-seconds"],
        1,
    ),
    Run(
        "61467575-835b-453e-a5ae-a1fe31a60e63@v8dev@",
        1748374895136,
        ["ilab::actual-train-seconds"],
        2,
    ),
]


class TestIlabRuns:

    def test_get_runs(self, server):

        # Get all runs, regardless of date
        response = requests.get(f"{server}/api/v1/ilab/runs", params={"all": "true"})
        assert response.status_code == 200
        result = response.json()

        # Our test database has the expected runs
        assert result["total"] == 21

        # Without pagination, we don't have "next_offset" field
        assert "next_offset" not in result

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
        last = 21

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
        assert result["total"] == len(RUNS)
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
        assert result["total"] == len(RUNS)
        assert result["count"] == 3
        assert result["results"][0]["id"] == RUNS[4].id
        assert result["next_offset"] == 7
