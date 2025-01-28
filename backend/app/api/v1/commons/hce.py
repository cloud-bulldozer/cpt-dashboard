from datetime import datetime, date
import pandas as pd
from app.services.search import ElasticService
import app.api.v1.commons.utils as utils
from app.api.v1.commons.constants import OCP_FIELD_CONSTANT_DICT


async def getData(
    start_datetime: date, end_datetime: date, size: int, offset: int, configpath: str
):
    query = {
        "size": size,
        "from": offset,
        "query": {"bool": {"filter": {"range": {"date": {"format": "yyyy-MM-dd"}}}}},
    }
    es = ElasticService(configpath=configpath)
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


async def getFilterData(start_datetime: date, end_datetime: date, configpath: str):
    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(OCP_FIELD_CONSTANT_DICT)

    response = await es.filterPost(start_datetime, end_datetime, aggregate)
    await es.close()

    return {"filterData": response["filterData"], "summary": response["summary"]}
