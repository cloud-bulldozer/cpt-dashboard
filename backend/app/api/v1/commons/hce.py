from datetime import datetime, date
import pandas as pd
from app.services.search import ElasticService


async def getData(start_datetime: date, end_datetime: date):
    query = {
        "query": {
            "bool": {
                "filter": {
                    "range": {
                        "date": {
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
        }
    }
    query['query']['bool']['filter']['range']['date']['lte'] = str(end_datetime)
    query['query']['bool']['filter']['range']['date']['gte'] = str(start_datetime)

    es = ElasticService(configpath="hce.elasticsearch")
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)
    jobs[['group']] = jobs[['group']].fillna(0)
    jobs.fillna('', inplace=True)
    if len(jobs) == 0:
        return jobs
    return jobs
