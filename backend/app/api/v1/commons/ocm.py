from datetime import date, datetime
import pandas as pd
from app.services.search import ElasticService
import app.api.v1.commons.utils as utils
from app.api.v1.commons.constants import OCM_FIELD_CONSTANT_DICT


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
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
                "filter": {"range": {"metrics.earliest": {"format": "yyyy-MM-dd"}}},
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

    aggregate = utils.buildAggregateQuery(OCM_FIELD_CONSTANT_DICT)
    refiner = ""
    if filter:
        refiner = utils.transform_filter(filter)

    response = await es.filterPost(
        start_datetime,
        end_datetime,
        aggregate,
        refiner,
        timestamp_field="metrics.earliest",
    )
    await es.close()

    return {
        "filterData": response.get("filterData", []),
        "summary": response.get("summary", {}),
    }


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
