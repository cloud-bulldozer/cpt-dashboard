from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional, Union

from elasticsearch import AsyncElasticsearch


@dataclass
class Request:
    index: str
    body: dict[str, Any]
    doc_type: Optional[str] = None
    params: Optional[Any] = None
    headers: Optional[Any] = None
    kwargs: Optional[dict[str, Any]] = None

    def __eq__(self, other) -> bool:
        iok = self.index == other.index
        bok = self.body == other.body
        dok = self.doc_type == other.doc_type
        pok = self.params == other.params
        hok = self.headers == other.headers

        # make empty dict and None match
        kok = (not self.kwargs and not other.kwargs) or self.kwargs == other.kwargs
        return iok and bok and dok and pok and hok and kok


class FakeAsyncElasticsearch(AsyncElasticsearch):
    hosts: Union[str, list[str]]
    args: dict[str, Any]
    closed: bool
    requests: list[Request]

    # This fake doesn't try to mimic Opensearch query and aggregation logic:
    # instead, the "data" is pre-loaded with a JSON response body that will
    # be returned on an "index" match. (This means that any external call we
    # need to mock has a single query against any one index!)
    data: dict[str, Any]

    def __init__(self, hosts: Union[str, list[str]], **kwargs):
        self.hosts = hosts
        self.args = kwargs
        self.closed = False
        self.data = defaultdict(list)
        self.requests = []
        # Error simulation flags
        self.post_error = None
        self.filterPost_error = None

    # Testing helpers to manage fake searches
    def set_query(
        self,
        root_index: str,
        hit_list: Optional[list[dict[str, Any]]] = None,
        aggregations: Optional[dict[str, Any]] = None,
        version: str = "v8dev",
        repeat: int = 1,
    ):
        """Add a canned response to an Opensearch query

        The overall response and items in the hit and aggregation lists will be
        augmented with the usual boilerplate.

        Multiple returns for a single index can be queued, in order, via
        successive calls. To return the same result on multiple calls, specify
        a "repeat" value greater than 1.

        Args:
            root_index: CDM index name (run, period, etc)
            hit_list: list of hit objects to be returned
            aggregation_list: list of aggregation objects to return
            version: CDM version
            repeat: how many times to return a mock before moving on
        """
        index = (
            f"cdm{version}-{root_index}"
            if version < "v9dev"
            else f"cdm-{version}-{root_index}"
        )
        hits = []
        if hit_list:
            for d in hit_list:
                source = d
                source["cdm"] = {"ver": version}
                hits.append(
                    {
                        "_index": index,
                        "_id": "random_string",
                        "_score": 1.0,
                        "_source": source,
                    }
                )
        aggregate_response = {}
        if aggregations:
            for agg, val in aggregations.items():
                if isinstance(val, list):
                    aggregate_response[agg] = {
                        "doc_count_error_upper_bound": 0,
                        "sum_other_doc_count": 0,
                        "buckets": val,
                    }
                else:
                    aggregate_response[agg] = val
        response = {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "hits": {
                "total": {"value": len(hits), "relation": "eq"},
                "max_score": 1.0,
                "hits": hits,
            },
        }
        if aggregate_response:
            response["aggregations"] = aggregate_response
        for c in range(repeat):
            self.data[index].append(response)

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

    # Faked AsyncElasticsearch methods
    async def post(
        self,
        query,
        size=10000,
        start_date=None,
        end_date=None,
        timestamp_field=None,
        **kwargs,
    ):
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
        **kwargs,
    ):
        if self.filterPost_error:
            raise self.filterPost_error
        return self.data.get(
            "commons_filterPost", [{"total": 0, "filterData": [], "summary": {}}]
        ).pop(0)

    async def close(self):
        self.closed = True

    async def info(self, **kwargs):
        pass

    async def ping(self, **kwargs):
        return True

    async def search(
        self, body=None, index=None, doc_type=None, params=None, headers=None, **kwargs
    ):
        """Return a canned response to a search query.

        Args:
            body: query body
            index: Opensearch index name
            doc_type: document type (rarely used)
            params: Opensearch search parameters (rarely used)
            headers: HTTP headers (rarely used)
            kwargs: whatever else you might pass to search

        Only the index is used here; to verify the correct Opensearch query
        bodies and parameters, the full request is recorded for inspection.

        Return:
            A JSON dict with the first canned result for the index, or an error
        """
        self.requests.append(
            Request(
                index=index,
                body=body,
                doc_type=doc_type,
                params=params,
                headers=headers,
                kwargs=kwargs,
            )
        )
        if index in self.data and len(self.data[index]) > 0:
            target = self.data[index].pop(0)
            return target
        return {
            "error": {
                "root_cause": [
                    {
                        "type": "index_not_found_exception",
                        "reason": f"no such index [{index}]",
                        "index": index,
                        "resource.id": index,
                        "resource.type": "index_or_alias",
                        "index_uuid": "_na_",
                    },
                ],
                "type": "index_not_found_exception",
                "reason": f"no such index [{index}]",
                "index": index,
                "resource.id": index,
                "resource.type": "index_or_alias",
                "index_uuid": "_na_",
            },
            "status": 404,
        }
