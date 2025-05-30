from collections import defaultdict
from datetime import datetime
import json
import requests


class TestOcpJobs:

    def test_get_runs(self, server):

        # Get all runs, regardless of date
        response = requests.get(
            f"{server}/api/v1/ocp/jobs",
            params={"start_date": "1970-01-01"},
            headers={"accept": "application/json"},
        )
        assert response.status_code == 200, f"Failed with {response.json()}"

        # OCP results are double-encoded: that is, the entire JSON body is
        # serialized as a pretty-printed string, so we have to double-convert.
        result = response.json()
        result = json.loads(result)
        assert {"startDate", "results", "endDate", "offset", "total"} == set(
            result.keys()
        )

        # Our test database has 273 runs
        assert len(result["results"]) == 273
        assert result["total"] == 273
        assert result["startDate"] == "1970-01-01"
        assert result["endDate"] == f"{datetime.now():%Y-%m-%d}"

        # All jobs "passed"
        statuses = defaultdict(int)
        for r in result["results"]:
            statuses[r.get("jobStatus")] += 1
        assert {"success", "failure"} == set(
            statuses.keys()
        ), f"Bad status check: {statuses}"
        assert statuses["success"] == 270
        assert statuses["failure"] == 3

    def test_pagination(self, server):
        next_offset = 0
        count = 0
        while next_offset < 273:
            response = requests.get(
                f"{server}/api/v1/ocp/jobs",
                {"start_date": "1970-01-01", "offset": next_offset, "size": 10},
            )
            assert response.status_code == 200, f"Failed with {response.json()}"
            result = response.json()
            result = json.loads(result)
            assert result["total"] == 273
            assert len(result["results"]) == 10 or count + len(result["results"]) == 273
            count += len(result["results"])
            assert result.get("offset") == next_offset + 10 or count == 273
            next_offset = result.get("offset")
        assert count == 273
