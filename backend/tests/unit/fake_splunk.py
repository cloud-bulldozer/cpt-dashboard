from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

from app.services.splunk import SplunkService


@dataclass
class SplunkRequest:
    """Represents a request made to the fake Splunk service for testing verification."""

    query: Optional[str]
    size: int
    offset: int
    sort: Optional[str]
    searchList: Optional[str]
    configpath: str

    def __eq__(self, other) -> bool:
        return (
            self.query == other.query
            and self.size == other.size
            and self.offset == other.offset
            and self.sort == other.sort
            and self.searchList == other.searchList
            and self.configpath == other.configpath
        )


class FakeSplunkService(SplunkService):
    configpath: str
    data: dict[str, Any]
    query_error: Optional[Exception]
    filterPost_error: Optional[Exception]

    """
    Fake SplunkService for testing telco functions without actual Splunk connections.
    This fake implementation follows the same pattern as FakeAsyncElasticsearch,
    providing canned responses for SplunkService methods used in telco.py:
    - query(): Used by telco.getData()
    - filterPost(): Used by telco.getFilterData()
    
    Usage:
        fake_splunk = FakeSplunkService()
        
        # For getData() tests
        fake_splunk.set_query_response(data_list=[...], total=100)
        
        # For getFilterData() tests
        fake_splunk.set_filter_response(data_list=[...], summary={...}, total=50)
        
        # For error testing:
        fake_splunk.set_query_response(error=Exception("Connection failed"))
    """

    def __init__(self, configpath: str = "TEST"):
        self.configpath = configpath
        self.data = defaultdict(list)
        # Error simulation flags
        self.query_error = None
        self.filterPost_error = None

    # Testing helpers to manage fake searches
    def set_query_response(
        self,
        data_list: Optional[list[dict[str, Any]]] = None,
        total: int = 0,
        error: Optional[Exception] = None,
        return_none: bool = False,
    ):
        """
        Set a canned response for SplunkService.query() method.

        This method is used by telco.getData() to retrieve time-series data.

        Args:
            data_list: List of telco data objects to return
            total: Total count of results
            error: Exception to raise instead of returning response data
            return_none: If True, return None instead of a response dict
        """
        if error is not None:
            self.query_error = error
            return

        # Clear any previous error
        self.query_error = None

        if return_none:
            response = None
        else:
            response = {"data": data_list or [], "total": total}

        self.data["query_responses"].append(response)

    def set_filter_response(
        self,
        data_list: Optional[list[dict[str, Any]]] = None,
        summary: Optional[dict[str, Any]] = None,
        total: int = 0,
        error: Optional[Exception] = None,
    ):
        """
        Set a canned response for SplunkService.filterPost() method.

        This method is used by telco.getFilterData() to retrieve aggregation data.

        Args:
            data_list: List of aggregation data objects to return
            summary: Summary statistics (e.g., {"success": 50, "failure": 10})
            total: Total count of results
            error: Exception to raise instead of returning response data
        """
        if error is not None:
            self.filterPost_error = error
            return

        # Clear any previous error
        self.filterPost_error = None

        response = {"data": data_list or [], "summary": summary or {}, "total": total}

        self.data["filter_responses"].append(response)

    # Mock SplunkService methods
    async def query(
        self,
        query: Optional[str] = None,
        size: int = 10,
        offset: int = 0,
        sort: Optional[str] = None,
        searchList: Optional[str] = None,
    ):
        # Check for error simulation
        if self.query_error:
            raise self.query_error

        # Return canned response or default empty response
        if self.data["query_responses"]:
            return self.data["query_responses"].pop(0)

        return {"data": [], "total": 0}

    async def filterPost(
        self,
        query: Optional[str] = None,
        searchList: Optional[str] = None,
    ):
        # Check for error simulation
        if self.filterPost_error:
            raise self.filterPost_error

        # Return canned response or default empty response
        if self.data["filter_responses"]:
            return self.data["filter_responses"].pop(0)

        return {"data": [], "summary": {}, "total": 0}
