from abc import abstractmethod
from typing import Any

from app.api.v1.endpoints.summary.summary import Summary
from app.services.search import ElasticService

"""KPI summary information using ElasticService.

This is a subclass of the Summary class targeted to products using the
ElasticService class to access OpenSearch data.

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
        print(f"opening ElasticService ({configpath})")
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
        else:
            self.date_filter = None

    @abstractmethod
    async def close(self):
        """Close the summary service."""
        print(f"closing {type(self.service).__name__}")
        await self.service.close()
