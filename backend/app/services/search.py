import bisect
from datetime import datetime, timedelta
import traceback

from fastapi.encoders import jsonable_encoder
from opensearchpy import AsyncOpenSearch

from app import config
import app.api.v1.commons.constants as constants


class ElasticService:
    # todo add bulkhead pattern
    # todo add error message for unauthorized user
    def __init__(self, configpath="", index=""):
        """Init method."""
        cfg = config.get_config()
        self.new_es, self.new_index, self.new_index_prefix = self.initialize_es(
            cfg, configpath, index
        )
        self.prev_es = None
        if cfg.get(configpath + ".internal"):
            self.prev_es, self.prev_index, self.prev_index_prefix = self.initialize_es(
                cfg, configpath + ".internal", index
            )

    def initialize_es(self, config, path, index):
        """Initializes es client using the configuration"""
        url = config.get(path + ".url")
        esUser = None
        index_prefix = ""
        if index == "":
            indice = config.get(path + ".indice")
        else:
            indice = index
        if config.is_set(path + ".prefix"):
            index_prefix = config.get(path + ".prefix")
        if config.is_set(path + ".username") and config.is_set(path + ".password"):
            esUser = config.get(path + ".username")
            esPass = config.get(path + ".password")
        if esUser:
            es = AsyncOpenSearch(url, verify_certs=False, http_auth=(esUser, esPass))
        else:
            es = AsyncOpenSearch(url, verify_certs=False)
        return es, indice, index_prefix

    async def post(
        self,
        query,
        indice=None,
        size=10000,
        start_date=None,
        end_date=None,
        timestamp_field=None,
    ):
        """Runs a query and returns the results"""
        if "aggs" in query or size == 0:
            """Handles aggregation queries logic

            The traditional usage convention is that aggregation queries were
            used only when no hits were expected (size == 0).

            However, OpenSearch supports using aggregation queries with hits
            also returned, and this can be useful, but can't be handled under
            the traditional usage convention which returns only "data" and
            "total", so we funnel that through here and return the full
            OpenSearch response.
            """
            if self.prev_es:
                prev_index = self.prev_index_prefix + (
                    self.prev_index if indice is None else indice
                )
                return await self.prev_es.search(
                    index=prev_index + "*", body=query, size=size
                )
            else:
                new_index = self.new_index_prefix + (
                    self.new_index if indice is None else indice
                )
                return await self.new_es.search(
                    index=new_index + "*", body=query, size=size
                )
        else:
            """Handles queries that require data from ES docs"""
            if timestamp_field:
                """Handles queries that have a timestamp field.

                We handle queries from both new and archive instances
                """
                if self.prev_es:
                    prev_index = self.prev_index_prefix + (
                        self.prev_index if indice is None else indice
                    )
                    today = datetime.today().date()
                    seven_days_ago = today - timedelta(days=7)
                    if start_date and start_date > seven_days_ago:
                        previous_results = {}
                    else:
                        new_end_date = (
                            min(end_date, seven_days_ago)
                            if end_date
                            else seven_days_ago
                        )
                        query["query"]["bool"]["filter"]["range"][timestamp_field][
                            "lte"
                        ] = str(new_end_date)
                        if start_date:
                            query["query"]["bool"]["filter"]["range"][timestamp_field][
                                "gte"
                            ] = str(start_date)
                        if start_date is None:
                            response = await self.prev_es.search(
                                index=prev_index + "*",
                                body=jsonable_encoder(query),
                                size=size,
                                request_timeout=50,
                            )
                            previous_results = {
                                "data": response["hits"]["hits"],
                                "total": response["hits"]["total"]["value"],
                            }
                        else:
                            response = await self.prev_es.search(
                                index=prev_index + "*",
                                body=jsonable_encoder(query),
                                size=size,
                                request_timeout=50,
                            )
                            previous_results = {
                                "data": response["hits"]["hits"],
                                "total": response["hits"]["total"]["value"],
                            }
                if self.prev_es and self.new_es:
                    new_index = self.new_index_prefix + (
                        self.new_index if indice is None else indice
                    )
                    today = datetime.today().date()
                    seven_days_ago = today - timedelta(days=7)
                    if end_date and end_date < seven_days_ago:
                        new_results = {}
                    else:
                        new_start_date = (
                            max(start_date, seven_days_ago)
                            if start_date
                            else seven_days_ago
                        )
                        query["query"]["bool"]["filter"]["range"][timestamp_field][
                            "gte"
                        ] = str(new_start_date)
                        if end_date:
                            query["query"]["bool"]["filter"]["range"][timestamp_field][
                                "lte"
                            ] = str(end_date)
                        if end_date is None:
                            response = await self.new_es.search(
                                index=new_index + "*",
                                body=jsonable_encoder(query),
                                size=size,
                                request_timeout=50,
                            )
                            new_results = {
                                "data": response["hits"]["hits"],
                                "total": response["hits"]["total"]["value"],
                            }
                        else:
                            response = await self.new_es.search(
                                index=new_index + "*",
                                body=jsonable_encoder(query),
                                size=size,
                                request_timeout=50,
                            )
                            new_results = {
                                "data": response["hits"]["hits"],
                                "total": response["hits"]["total"]["value"],
                            }
                    combined_data = (previous_results.get("data") or []) + (
                        new_results.get("data") or []
                    )
                    unique_data = await self.remove_duplicates(combined_data)

                    totalVal = previous_results.get("total", 0) + new_results.get(
                        "total", 0
                    )
                    return {"data": unique_data, "total": totalVal}
                else:
                    new_index = self.new_index_prefix + (
                        self.new_index if indice is None else indice
                    )
                    if start_date and end_date:
                        query["query"]["bool"]["filter"]["range"][timestamp_field][
                            "gte"
                        ] = str(start_date)
                        query["query"]["bool"]["filter"]["range"][timestamp_field][
                            "lte"
                        ] = str(end_date)
                        response = await self.new_es.search(
                            index=new_index + "*",
                            body=jsonable_encoder(query),
                            size=size,
                            request_timeout=50,
                        )
                        return {
                            "data": response["hits"]["hits"],
                            "total": response["hits"]["total"]["value"],
                        }
            else:
                """Handles queries that do not have a timestamp field"""
                previous_results = {}
                if self.prev_es:
                    prev_index = self.prev_index_prefix + (
                        self.prev_index if indice is None else indice
                    )
                    response = await self.prev_es.search(
                        index=prev_index + "*",
                        body=jsonable_encoder(query),
                        size=size,
                        request_timeout=50,
                    )
                    previous_results = {
                        "data": response["hits"]["hits"],
                        "total": response["hits"]["total"]["value"],
                    }
                new_index = self.new_index_prefix + (
                    self.new_index if indice is None else indice
                )
                response = await self.new_es.search(
                    index=new_index + "*",
                    body=jsonable_encoder(query),
                    size=size,
                    request_timeout=50,
                )
                new_results = {
                    "data": response["hits"]["hits"],
                    "total": response["hits"]["total"]["value"],
                }
                combined_data = (previous_results.get("data") or []) + (
                    new_results.get("data") or []
                )
                unique_data = await self.remove_duplicates(combined_data)

                prev_total = previous_results.get("total", 0)
                new_total = new_results.get("total", 0)
                totalVal = prev_total + new_total

                return {"data": unique_data, "total": totalVal}

    async def remove_duplicates(self, all_results):
        seen = set()
        filtered_results = []
        for each_result in all_results:
            flat_doc = flatten_dict(each_result)
            if tuple(sorted(flat_doc.items())) in seen:
                continue
            else:
                filtered_results.append(each_result)
                seen.add(tuple(sorted(flat_doc.items())))
        return filtered_results

    def get_unique_values(self, all_values):
        seen = set()
        values = []
        for val in all_values:
            lower_value = str(val).lower()
            if lower_value not in seen:
                seen.add(lower_value)
                values.append(val)
        return values

    async def buildFilterData(self, filter, total):
        """Return the data to build the filter"""
        try:
            summary = await self.getSummary(filter, total)
            filterData = []
            upstreamList = [
                x.get("key")
                for x in filter.get("upstream", {}).get("buckets", [])
                if "key" in x
            ]
            clusterTypeList = [
                x.get("key")
                for x in filter.get("clusterType", {}).get("buckets", [])
                if "key" in x
            ]

            if "build" in filter and "buckets" in filter["build"]:
                buildObj = await self.buildFilterValues(filter)
                filterData.append(buildObj)

            keys_to_remove = [
                "min_timestamp",
                "max_timestamp",
                "upstream",
                "clusterType",
                "build",
            ]
            refiner = removeKeys(filter, keys_to_remove)

            for key, value in refiner.items():
                field = key
                all_values = [bucket["key"] for bucket in value["buckets"]]
                # to deduplicate values based on case-insensitive match
                values = self.get_unique_values(all_values)

                if key == "platform":
                    platformOptions = buildPlatformFilter(upstreamList, clusterTypeList)
                    values = values + platformOptions
                elif key == "ocpVersion":
                    short_versions = [
                        str(value)[: constants.OCP_SHORT_VER_LEN] for value in values
                    ]
                    values = list(set(short_versions))
                elif key == "result" or key == "jobStatus":
                    values = list(
                        set(
                            [
                                constants.JOB_STATUS_MAP.get(
                                    x.lower(), constants.JOB_STATUS_OTHERS
                                )
                                for x in values
                            ]
                        )
                    )
                    field = "jobStatus"
                filterData.append(
                    {
                        "key": field,
                        "value": values,
                        "name": constants.FILEDS_DISPLAY_NAMES[key],
                    }
                )
            return {
                "filterData": filterData,
                "summary": summary,
                "upstreamList": upstreamList,
            }
        except Exception as e:
            print(f"Error building filter data: {e}")
            return {"filterData": [], "summary": {}, "upstreamList": []}

    async def getSummary(self, filter, total):
        summary = {"total": total, "success": 0, "failure": 0, "other": 0}

        for key in ("jobStatus", "result"):
            buckets = filter.get(key, {}).get("buckets")
            if buckets:
                for x in buckets:
                    field = constants.JOB_STATUS_MAP.get(
                        x["key"].lower(), constants.JOB_STATUS_OTHERS
                    )
                    summary[field] = summary.get(field, 0) + x.get("doc_count", 0)
                break

        return summary

    async def buildFilterValues(self, filter):
        buildList = [
            x.get("key")
            for x in filter.get("build", {}).get("buckets", [])
            if "key" in x
        ]
        build = getBuildFilter(buildList)
        buildObj = {"key": "build", "value": build, "name": "Build"}
        return buildObj

    async def buildFilterQuery(
        self, start_datetime, end_datetime, aggregate, refiner, timestamp_field
    ):
        start_date = (
            start_datetime.strftime("%Y-%m-%d")
            if start_datetime
            else (datetime.utcnow().date() - timedelta(days=5).strftime("%Y-%m-%d"))
        )
        end_date = (
            end_datetime.strftime("%Y-%m-%d")
            if end_datetime
            else datetime.utcnow().strftime("%Y-%m-%d")
        )

        query = {
            "aggs": {},
            "query": {
                "bool": {
                    "filter": {
                        "range": {
                            timestamp_field: {
                                "format": "yyyy-MM-dd",
                                "lte": end_date,
                                "gte": start_date,
                            }
                        }
                    },
                }
            },
        }
        query["aggs"].update(aggregate)
        if refiner:
            query["query"]["bool"]["should"] = refiner["query"]
            query["query"]["bool"]["minimum_should_match"] = refiner["min_match"]
            query["query"]["bool"]["must_not"] = refiner["must_query"]
        return query

    def merge_aggregations(self, agg1: dict, agg2: dict) -> dict:
        merged = {}

        for key in set(agg1.keys()).union(agg2.keys()):
            if key in agg1 and key in agg2:
                # Both have this aggregation
                if "buckets" in agg1[key] and "buckets" in agg2[key]:
                    # Merge buckets by key
                    bucket_map = {}

                    for bucket in agg1[key]["buckets"]:
                        bucket_map[bucket["key"]] = bucket["doc_count"]

                    for bucket in agg2[key]["buckets"]:
                        if bucket["key"] in bucket_map:
                            bucket_map[bucket["key"]] += bucket["doc_count"]
                        else:
                            bucket_map[bucket["key"]] = bucket["doc_count"]

                    # Convert back to bucket format
                    merged[key] = {
                        "buckets": [
                            {"key": k, "doc_count": v} for k, v in bucket_map.items()
                        ]
                    }
                else:
                    # If it's a single value
                    merged[key] = {
                        "value": agg1[key].get("value", 0) + agg2[key].get("value", 0)
                    }
            else:
                # Only one of them has this key
                merged[key] = agg1.get(key, agg2.get(key))

        return merged

    async def filterPost(
        self,
        start_datetime,
        end_datetime,
        aggregate,
        refiner,
        timestamp_field="timestamp",
        indice=None,
    ):
        try:
            query = await self.buildFilterQuery(
                start_datetime, end_datetime, aggregate, refiner, timestamp_field
            )
            if self.prev_es:
                self.prev_index = self.prev_index_prefix + (
                    self.prev_index if indice is None else indice
                )
                today = datetime.today().date()
                seven_days_ago = today - timedelta(days=7)
                if start_datetime and start_datetime > seven_days_ago:
                    previous_results = {}
                else:
                    new_end_date = (
                        min(end_datetime, seven_days_ago)
                        if end_datetime
                        else seven_days_ago
                    )
                    query["query"]["bool"]["filter"]["range"][timestamp_field][
                        "lte"
                    ] = str(new_end_date)
                    query["query"]["bool"]["filter"]["range"][timestamp_field][
                        "gte"
                    ] = str(start_datetime)

                    response = await self.prev_es.search(
                        index=self.prev_index + "*",
                        body=jsonable_encoder(query),
                        size=0,
                        request_timeout=50,
                    )
                    previous_results = {
                        "data": response["aggregations"],
                        "total": response["hits"]["total"]["value"],
                    }
            if self.prev_es and self.new_es:
                self.new_index = self.new_index_prefix + (
                    self.new_index if indice is None else indice
                )
                today = datetime.today().date()
                seven_days_ago = today - timedelta(days=7)
                if end_datetime and end_datetime < seven_days_ago:
                    new_results = {}
                else:
                    new_start_date = (
                        max(start_datetime, seven_days_ago)
                        if start_datetime
                        else seven_days_ago
                    )
                    query["query"]["bool"]["filter"]["range"][timestamp_field][
                        "gte"
                    ] = str(new_start_date)

                    query["query"]["bool"]["filter"]["range"][timestamp_field][
                        "lte"
                    ] = str(end_datetime)

                    response = await self.new_es.search(
                        index=self.new_index + "*",
                        body=jsonable_encoder(query),
                        size=0,
                        request_timeout=50,
                    )
                    new_results = {
                        "total": response["hits"]["total"]["value"],
                        "data": response["aggregations"],
                    }
                prev_total = previous_results.get("total", 0)
                new_total = new_results.get("total", 0)
                total = prev_total + new_total
                results = self.merge_aggregations(
                    previous_results.get("data", {}), new_results.get("data", {})
                )
                x = await self.buildFilterData(results, total)

                return {
                    "filterData": x["filterData"],
                    "summary": x["summary"],
                    "upstreamList": x["upstreamList"],
                    "total": total,
                }
            else:
                response = await self.new_es.search(
                    index=self.new_index + "*",
                    body=jsonable_encoder(query),
                    size=0,
                    request_timeout=50,
                )
                total = response["hits"]["total"]["value"]
                results = response["aggregations"]
                x = await self.buildFilterData(results, total)

                return {
                    "filterData": x["filterData"],
                    "summary": x["summary"],
                    "upstreamList": x["upstreamList"],
                    "total": total,
                }

        except Exception as e:
            print(f"Error retrieving filter data: {e}")
            print(traceback.format_exc())

    async def close(self):
        """Closes es client connections"""
        await self.new_es.close()
        if self.prev_es is not None:
            await self.prev_es.close()


class IndexTimestamp:
    """Custom class to store and index with its start and end timestamps"""

    def __init__(self, index, timestamps):
        self.index = index
        self.timestamps = timestamps

    def __lt__(self, other):
        return self.timestamps[0] < other.timestamps[0]


class SortedIndexList:
    """Custom class to sort indexes based on their start timestamps"""

    def __init__(self):
        self.indices = []

    def insert(self, index_timestamps):
        bisect.insort(self.indices, index_timestamps)

    def get_indices_in_given_range(self, start_date, end_date):
        return [
            index_timestamp
            for index_timestamp in self.indices
            if (
                (
                    start_date
                    and end_date
                    and start_date <= index_timestamp.timestamps[0]
                    and index_timestamp.timestamps[1] <= end_date
                )
                or (
                    start_date
                    and index_timestamp.timestamps[0] < start_date
                    and start_date <= index_timestamp.timestamps[1]
                )
                or (
                    end_date
                    and index_timestamp.timestamps[1] > end_date
                    and index_timestamp.timestamps[0] <= end_date
                )
            )
        ]


def flatten_dict(d, parent_key="", sep="."):
    """Method to flatten a ES doc for comparing duplicates"""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, val in enumerate(v):
                items.extend(flatten_dict({str(i): val}, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def removeKeys(filterDict: dict[str, any], keys_to_remove: list[str]) -> dict[str, any]:
    return {k: v for k, v in filterDict.items() if k not in keys_to_remove}


def buildPlatformFilter(upstream_list, cluster_type_list):
    filter_options = set()

    if any("rosa-hcp" in item.lower() for item in upstream_list):
        filter_options.add("AWS ROSA-HCP")

    if any("rosa" in item.lower() for item in cluster_type_list):
        filter_options.add("AWS ROSA")

    return list(filter_options)


def getBuildFilter(input_list):
    result = ["-".join(item.split("-")[-4:]) for item in input_list]
    return result
