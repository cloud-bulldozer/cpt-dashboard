from datetime import date, datetime
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
        "query": {
            "bool": {
                "filter": {"range": {"metrics.earliest": {"format": "yyyy-MM-dd"}}}
            }
        },
    }

    es = ElasticService(configpath=configpath)
    response = await es.post(
        query=query,
        size=size,
        start_date=start_datetime,
        end_date=end_datetime,
        timestamp_field="metrics.earliest",
    )
    await es.close()
    tasks = [item["_source"] for item in response["data"]]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return {"data": jobs, "total": response["total"]}

    if "buildUrl" not in jobs.columns:
        jobs.insert(len(jobs.columns), "buildUrl", "")
    if "ciSystem" not in jobs.columns:
        jobs.insert(len(jobs.columns), "ciSystem", "")
    jobs.fillna("", inplace=True)
    jobs["jobStatus"] = jobs.apply(convertJobStatus, axis=1)
    return {"data": jobs, "total": response["total"]}


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):
    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(OCP_FIELD_CONSTANT_DICT)

    response = await es.filterPost(start_datetime, end_datetime, aggregate)
    await es.close()

    return {"filterData": response["filterData"], "summary": response["summary"]}


def fillCiSystem(row):
    currDate = datetime.strptime(row["metrics.earliest"][:26], "%Y-%m-%dT%H:%M:%S.%f")
    if currDate > datetime(2024, 6, 24):
        return "Jenkins"
    else:
        return "Airflow"


def convertJobStatus(row):
    if row["metrics.success"] >= 0.80:
        return "success"
    elif row["metrics.success"] < 0.40:
        return "failure"
    else:
        return "unstable"
