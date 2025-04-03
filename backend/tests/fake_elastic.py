from typing import Any, Optional, Union

from elasticsearch import AsyncElasticsearch


class FakeAsyncElasticsearch(AsyncElasticsearch):
    hosts: Union[str, list[str]]
    args: dict[str, Any]
    closed: bool

    # This fake doesn't try to mimic Opensearch query and aggregation logic:
    # instead, the "data" is pre-loaded with a JSON response body that will
    # be returned on an "index" match. (This means that any external call we
    # need to mock has a single query against any one index!)
    data: dict[str, Any]

    def __init__(self, hosts: Union[str, list[str]], **kwargs):
        self.hosts = hosts
        self.args = kwargs
        self.closed = False
        self.data = {}

    # Testing helpers to manage fake searches
    def set_query(
        self,
        root_index: str,
        hit_list: Optional[list[dict[str, Any]]] = None,
        aggregation_list: Optional[dict[str, Any]] = None,
        version: int = 7,
    ):
        ver = f"v{version:d}dev"
        index = f"cdm{ver}-{root_index}"
        hits = []
        aggregations = None
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
        if aggregation_list:
            aggregations = {
                k: {
                    "doc_count_error_upper_bound": 0,
                    "sum_other_doc_count": 0,
                    "buckets": v,
                }
                for k, v in aggregation_list.items()
            }
        self.data[index] = {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "hits": {
                "total": {"value": len(hits), "relation": "eq"},
                "max_score": 1.0,
                "hits": hits,
            },
        }
        if aggregations:
            self.data[index]["aggregations"] = aggregations

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
        if index in self.data:
            target = self.data[index]
            del self.data[index]
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
