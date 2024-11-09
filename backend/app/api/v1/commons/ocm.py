from datetime import date, datetime
import pandas as pd
from app.services.search import ElasticService


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
        return jobs

    if "buildUrl" not in jobs.columns:
        jobs.insert(len(jobs.columns), "buildUrl", "")
    if "ciSystem" not in jobs.columns:
        jobs.insert(len(jobs.columns), "ciSystem", "")
    jobs.fillna("", inplace=True)
    jobs["jobStatus"] = jobs.apply(convertJobStatus, axis=1)
    return {"data": jobs, "total": response["total"]}


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
