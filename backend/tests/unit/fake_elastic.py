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

    # Testing helpers to manage fake searches
    def set_query(
        self,
        root_index: str,
        hit_list: Optional[list[dict[str, Any]]] = None,
        aggregations: Optional[dict[str, Any]] = None,
        version: int = 7,
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
            repeat:
        """
        ver = f"v{version:d}dev"
        index = f"cdm{ver}-{root_index}"
        hits = []
        if hit_list:
            for d in hit_list:
                source = d
                source["cdm"] = {"ver": ver}
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

    # Faked AsyncElasticsearch methods
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
