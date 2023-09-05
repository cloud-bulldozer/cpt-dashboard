from datetime import datetime,timedelta
import trio
import semver
import pandas as pd
from app.services.search import ElasticService

from app.async_util import trio_run_with_asyncio


columnOrder = ["ciSystem", "uuid", "platform", "ocpVersion", "nodeName", "releaseStream", "clusterType", "benchmark", "masterNodesCount", "workerNodesCount", "infraNodesCount", "masterNodesType", "workerNodesType", "infraNodesType", "totalNodesCount", "clusterName", "networkType", "buildTag", "jobStatus", "buildUrl", "upstreamJob", "upstreamJobBuild", "executionDate", "jobDuration", "startDate", "endDate", "timestamp", "shortVersion"]
# "clusterType", "benchmark" columns are missing on AIRFLOW jobs
AirflowColumnOrder = ["ci_system", "uuid", "platform", "cluster_version", "node_name", "release_stream", "clusterType", "benchmark", "master_count", "worker_count", "infra_count", "master_type", "worker_type", "infra_type", "total_count", "cluster_name", "network_type", "build_tag",  "job_status", "build_url", "upstream_job", "upstream_job_build", "execution_date", "job_duration", "start_date", "end_date", "timestamp", "shortVersion"]



async def getData(type, airflow=False):
    filterName = "ciSystem"
    if type == "AIRFLOW":
        filterName = "ci_system"
    query = {
  "query": {
    "bool": {
      "must": [
        {
          "query_string": {
            "query": filterName + " == " + type
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

    es = ElasticService(airflow)
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)

    cleanJobs = jobs[jobs['platform'] != ""]

    if type == "AIRFLOW":
        jbs = cleanJobs.reindex(columns=AirflowColumnOrder)
        jbs['shortVersion'] = jobs['cluster_version'].str.slice(0, 4)
        jbs = renameColumns(jbs)
    else:
        jbs = cleanJobs.reindex(columns=columnOrder)
        jbs['shortVersion'] = jobs['ocpVersion'].str.slice(0, 4)

    jbs = jbs.drop(columns=["nodeName"])

    if type == "PROW":
        jobs['upstreamJob'] = jobs['upstreamJob'].map(shorten)

    df = {'response': group_by_platform(jbs)}

    return df


def shorten(job: str):
    i = job.index("-main-")
    sub = job[i + 6:]
    return sub


def renameColumns(df):
    for i, x in enumerate(columnOrder):
        df = df.rename(columns={AirflowColumnOrder[i]: x})
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
