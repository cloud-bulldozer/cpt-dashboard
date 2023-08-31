from datetime import datetime,timedelta
import trio
import semver
import pandas as pd
from app.services.search import ElasticService

from app.async_util import trio_run_with_asyncio


async def getData(type):
    query = {
  "query": {
    "bool": {
      "must": [
        {
          "query_string": {
            "query": "ciSystem == " + type
          }
        },
        {
          "range": {
            "timestamp": {
              "gte": "now-10d"
            }
          }
        }
      ]
    }
  }
}

    es = ElasticService()
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)
    cleanJobs = jobs[jobs['platform'] != ""]

    drop = ['endDate','clusterName','upstreamJobBuild','executionDate',
            'startDate','buildTag','upstreamJob','releaseStream','timestamp',
            'jobDuration','networkType','workerNodesType','infraNodesType','masterNodesType',
            'workerNodesCount','infraNodesCount','masterNodesCount']
    cleanJobs = cleanJobs.drop(columns=drop)
    cleanJobs['shortVersion'] = cleanJobs['ocpVersion'].str.slice(0,4)

    df = {'response': group_by_platform(cleanJobs)}

    return df

def group_by_platform(data_frame: pd.DataFrame):
    return [
        get_table(group[0], group[1].drop(columns=['platform']))
        for group in data_frame.groupby(by=['platform'])
    ]


def get_table(title: str, data_frame: pd.DataFrame):
    return {
        'title': title,
        'data' : get_framelist(data_frame)
    }

def get_framelist(data_frame: pd.DataFrame):
    return [
        get_frame(group[0], (group[1].drop(
            columns=['ocpVersion'])))
        for group in data_frame.groupby(by=['shortVersion'])
    ]


def get_frame(title: str, data_frame: pd.DataFrame):
    return {
        'version'   : title.title(),
        'cloud_data': data_frame.values.tolist(),
        'columns'   : [name.replace('_', ' ').title()
                       for name in data_frame.columns.tolist()]
    }