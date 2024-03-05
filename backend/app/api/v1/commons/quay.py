from datetime import date
import pandas as pd
import app.api.v1.commons.utils as utils
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

    es = ElasticService(configpath=configpath)
    response = await es.post(query=query, start_date=start_datetime, end_date=end_datetime, timestamp_field='timestamp')
    await es.close()
    tasks = [item['_source'] for item in response]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return jobs

    jobs[['masterNodesCount', 'workerNodesCount',
          'infraNodesCount', 'totalNodesCount']] = jobs[['masterNodesCount', 'workerNodesCount', 'infraNodesCount', 'totalNodesCount']].fillna(0)
    jobs.fillna('', inplace=True)
    jobs['benchmark'] = jobs.apply(utils.updateBenchmark, axis=1)
    jobs['platform'] = jobs.apply(utils.clasifyAWSJobs, axis=1)
    jobs['jobStatus'] = jobs.apply(utils.updateStatus, axis=1)
    jobs['build'] = jobs.apply(utils.getBuild, axis=1)
    jobs['shortVersion'] = jobs['ocpVersion'].str.slice(0, 4)

    return jobs[jobs['platform'] != ""]
