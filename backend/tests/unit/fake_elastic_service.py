from collections import defaultdict
from typing import Any, Optional

from app.services.search import ElasticService


class FakeElasticService(ElasticService):
    """
    Fake ElasticService for testing commons functions without actual Elasticsearch connections.

    This fake implementation provides canned responses for ElasticService methods used in commons modules:
    - post(): Used by getData() methods
    - filterPost(): Used by getFilterData() methods

    """

    def __init__(self, configpath: str = "TEST", index: str = ""):
        self.configpath = configpath
        self.index = index
        self.data = defaultdict(list)
        # Error simulation flags
        self.post_error = None
        self.filterPost_error = None

    # Testing helpers to manage fake post/filterPost responses
    def set_post_response(
        self,
        response_type: str,
        data_list: Optional[list[dict[str, Any]]] = None,
        total: int = 0,
        filter_data: Optional[list[dict[str, Any]]] = None,
        summary: Optional[dict[str, Any]] = None,
        upstream_list: Optional[list[str]] = None,
        repeat: int = 1,
        error: Optional[Exception] = None,
    ):
        """Set a canned response or error for ElasticService methods (post/filterPost)

        Args:
            response_type: "post" for getData responses, "filterPost" for getFilterData responses
            data_list: list of source data objects (for post responses)
            total: total count
            filter_data: filter aggregation data (for filterPost responses)
            summary: summary data (for filterPost responses)
            upstream_list: list of upstream job names (for filterPost responses)
            repeat: how many times to return this response
            error: Exception to raise instead of returning response data
        """
        if error is not None:
            # Set error instead of response data
            if response_type == "post":
                self.post_error = error
            elif response_type == "filterPost":
                self.filterPost_error = error
            else:
                raise ValueError(
                    f"Invalid response_type: {response_type}. Must be 'post' or 'filterPost'"
                )
            return

        # Set normal response data
        if response_type == "post":
            # Format for getData responses
            hits = []
            if data_list:
                for d in data_list:
                    hits.append({"_source": d})
            response = {"data": hits, "total": total}
        elif response_type == "filterPost":
            # Format for getFilterData responses
            response = {
                "total": total,
                "filterData": filter_data or [],
                "summary": summary or {},
            }
            if upstream_list:
                response["upstreamList"] = upstream_list
        else:
            raise ValueError(
                f"Invalid response_type: {response_type}. Must be 'post' or 'filterPost'"
            )

        # Store in a special key for commons responses
        commons_key = f"commons_{response_type}"
        if commons_key not in self.data:
            self.data[commons_key] = []
        for c in range(repeat):
            self.data[commons_key].append(response)

    # Mock ElasticService methods
    async def post(
        self,
        query,
        indice=None,
        size=10000,
        start_date=None,
        end_date=None,
        timestamp_field=None,
        **kwargs,
    ):
        """Mock the ElasticService.post method"""
        if self.post_error:
            raise self.post_error
        return self.data.get("commons_post", [{"data": [], "total": 0}]).pop(0)

    async def filterPost(
        self,
        start_datetime,
        end_datetime,
        aggregate,
        refiner,
        timestamp_field="timestamp",
        indice=None,
        **kwargs,
    ):
        """Mock the ElasticService.filterPost method"""
        if self.filterPost_error:
            raise self.filterPost_error
        return self.data.get(
            "commons_filterPost", [{"total": 0, "filterData": [], "summary": {}}]
        ).pop(0)

    async def close(self):
        """Mock the ElasticService.close method - no-op for testing"""
        pass
