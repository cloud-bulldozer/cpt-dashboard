from datetime import datetime, date
import pandas as pd
from app.services.search import ElasticService


async def getData(start_datetime: date, end_datetime: date):
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

    es = ElasticService(configpath="ocp.elasticsearch")
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)
    jobs[['masterNodesCount', 'workerNodesCount',
          'infraNodesCount', 'totalNodesCount']] = jobs[['masterNodesCount', 'workerNodesCount', 'infraNodesCount', 'totalNodesCount']].fillna(0)
    jobs.fillna('', inplace=True)

    if len(jobs) == 0:
        return jobs

    cleanJobs = jobs[jobs['platform'] != ""]

    jbs = cleanJobs
    jbs['shortVersion'] = jbs['ocpVersion'].str.slice(0, 4)

    return jbs
