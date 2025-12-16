from datetime import date

import pandas as pd

from app.api.v1.commons.constants import OSO_FIELD_CONSTANT_DICT
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
    sort: str,
    filter: str,
    configpath: str,
):
    should = []
    must_not = []
    query = {
        "size": size,
        "from": offset,
        "query": {
            "bool": {
                "filter": {"range": {"timestamp": {"format": "yyyy-MM-dd"}}},
                "should": should,
                "must_not": must_not,
            }
        },
    }

    if filter:
        refiner = utils.transform_filter(filter)
        should.extend(refiner["query"])
        must_not.extend(refiner["must_query"])
        query["query"]["bool"]["minimum_should_match"] = refiner["min_match"]

    es = ElasticService(configpath=configpath)

    response = await es.post(
        query=query,
        size=size,
        start_date=start_datetime,
        end_date=end_datetime,
        timestamp_field="timestamp",
    )
    await es.close()
    tasks = [item["_source"] for item in response["data"]]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return {"data": jobs, "total": response["total"]}

    return {"data": jobs, "total": response["total"]}


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):
    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(OSO_FIELD_CONSTANT_DICT)
    refiner = ""
    if filter:
        refiner = utils.transform_filter(filter)

    response = await es.filterPost(
        start_datetime, end_datetime, aggregate, refiner, timestamp_field="timestamp"
    )
    await es.close()
    if not response.get("filterData", []) or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}
    return {
        "total": response.get("total", 0),
        "filterData": response.get("filterData", 0),
        "summary": response.get("summary", {}),
    }
