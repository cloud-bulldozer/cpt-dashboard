from datetime import datetime, date
import pandas as pd
from app.services.search import ElasticService
import app.api.v1.commons.utils as utils
from app.api.v1.commons.constants import HCE_FIELD_CONSTANT_DICT


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
    filter: str,
    configpath: str,
):
    query = {
        "size": size,
        "from": offset,
        "query": {"bool": {"filter": {"range": {"date": {"format": "yyyy-MM-dd"}}}}},
    }
    aggregate = utils.buildAggregateQuery(HCE_FIELD_CONSTANT_DICT)
    query["aggs"] = aggregate
    es = ElasticService(configpath=configpath)
    print("im hce")

    response = await es.post(
        query=query,
        size=size,
        start_date=start_datetime,
        end_date=end_datetime,
        timestamp_field="date",
    )

    await es.close()
    tasks = [item["_source"] for item in response["data"]]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return {"data": jobs, "total": response["total"]}

    jobs[["group"]] = jobs[["group"]].fillna(0)
    jobs.fillna("", inplace=True)
    return {"data": jobs, "total": response["total"]}


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):
    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(HCE_FIELD_CONSTANT_DICT)
    refiner = ""
    if filter:
        refiner = utils.transform_filter(filter)

    response = await es.filterPost(
        start_datetime, end_datetime, aggregate, refiner, timestamp_field="date"
    )
    await es.close()

    return {
        "total": response.get("total", 0),
        "filterData": response.get("filterData", 0),
        "summary": response.get("summary", {}),
    }
