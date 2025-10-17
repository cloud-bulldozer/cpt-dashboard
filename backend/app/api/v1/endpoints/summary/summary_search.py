from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any, Optional

from app.api.v1.endpoints.summary.summary import Summary
from fastapi import APIRouter, Depends

from app.services.search import ElasticService

"""Information about product release KPIs.

Each product version has a set of benchmarks that have been run for various
system configurations. This data is recovered from the job index and used to
access average and historical data for a product version to help assess
product release readiness.

NOTE: Other factors directly affecting release health include the health of the
CI system, and any open Jira stories or bugs. Those factors aren't handled by
this code.

AI assistance: Cursor is extremely helpful in generating suggesting code
snippets along the way. While most of this code is hand generated as the
relationships are tricky and difficult to describe to the AI, it's been
extremely helpful as an "over the shoulder assistant" to simplify routine
coding tasks.

Assisted-by: Cursor + claude-4-sonnet
"""


class SummarySearch(Summary):
    service: ElasticService = None
    date_filter: dict[str, Any] | None = None

    def __init__(
        self,
        product: str,
        configpath: str = "ocp.elasticsearch",
    ):
        super().__init__(product, configpath)
        self.service = ElasticService(configpath)
        self.date_filter = None

    def set_date_filter(self, start_date: str | None, end_date: str | None):
        if start_date or end_date:
            self.end_date = end_date
            self.date_filter = None
            range = {"format": "yyyy-MM-dd"}
            if start_date:
                range["gte"] = start_date
            if end_date:
                range["lte"] = end_date
            self.date_filter = {
                "range": {
                    "timestamp": range,
                }
            }
            print(f"date_filter: {self.date_filter}")
        else:
            self.date_filter = None
            print("no date_filter")

    @abstractmethod
    async def close(self):
        """Close the summary service."""
        print(f"closing {type(self.service).__name__}")
        self.service.close()
