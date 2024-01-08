from datetime import date
import pandas as pd
from app.services.search import ElasticService


async def getData(start_datetime: date, end_datetime: date, configpath: str):
    query = {
        "query": {
            "bool": {
                "filter": {
                    "range": {
                        "timestamp": {
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
        }
    }
    query['query']['bool']['filter']['range']['timestamp']['lte'] = str(end_datetime)
    query['query']['bool']['filter']['range']['timestamp']['gte'] = str(start_datetime)

    es = ElasticService(configpath=configpath)
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return jobs

    jobs[['masterNodesCount', 'workerNodesCount',
          'infraNodesCount', 'totalNodesCount']] = jobs[['masterNodesCount', 'workerNodesCount', 'infraNodesCount', 'totalNodesCount']].fillna(0)
    jobs.fillna('', inplace=True)
    jobs["benchmark"] = jobs.apply(updateBenchmark, axis=1)
    jobs["jobType"] = jobs.apply(jobType, axis=1)
    jobs["isRehearse"] = jobs.apply(isRehearse, axis=1)
    jobs["jobStatus"] = jobs.apply(updateStatus, axis=1)

    cleanJobs = jobs[jobs['platform'] != ""]

    jbs = cleanJobs
    jbs['shortVersion'] = jbs['ocpVersion'].str.slice(0, 4)

    return jbs


def updateStatus(row):
    return row["jobStatus"].lower()


def updateBenchmark(row):
    if row["upstreamJob"].__contains__("upgrade"):
        return "upgrade-" + row["benchmark"]
    return row["benchmark"]


def jobType(row):
    if row["upstreamJob"].__contains__("periodic"):
        return "periodic"
    return "pull request"


def isRehearse(row):
    if row["upstreamJob"].__contains__("rehearse"):
        return "True"
    return "False"
