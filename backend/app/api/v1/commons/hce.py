from datetime import datetime, date
import pandas as pd
from app.services.search import ElasticService


async def getData(start_datetime: date, end_datetime: date, configpath: str):
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

    es = ElasticService(configpath=configpath)
    response = await es.post(query=query, start_date=start_datetime, end_date=end_datetime, timestamp_field='date')
    await es.close()
    tasks = [item['_source'] for item in response]
    jobs = pd.json_normalize(tasks)
    jobs[['group']] = jobs[['group']].fillna(0)
    jobs.fillna('', inplace=True)
    if len(jobs) == 0:
        return jobs
    return jobs
