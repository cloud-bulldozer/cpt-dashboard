from datetime import datetime,timedelta
import trio
import semver
from fastapi import APIRouter
import io
import pprint
from json import loads
import pandas as pd
from app.services.search import ElasticService
router = APIRouter()

@router.get('/api/v1/graph/{uuid}')
async def graph(uuid: str):
    index = ""
    meta = await getMetadata(uuid)
    print(meta)
    metrics = []
    if meta["benchmark"] == "k8s-netperf" :
        uuids = await getMatchRuns(meta,False)
        print(uuids)
        index = "k8s-netperf"
        oData = await getResults(uuid,uuids,index)
        cData = await getResults(uuid,[uuid],index)
        oMetrics = await processNetperf(oData)
        oMetrics = oMetrics.reset_index()
        nMetrics = await processNetperf(cData)
        nMetrics = nMetrics.reset_index()
        x=[]
        y=[]
        for index, row in oMetrics.iterrows():
            test = "{}-{}".format(row['profile'], row['messageSize'])
            value = "{}".format(row['throughput'])
            x.append(value)
            y.append(test)
        old = {'y' : x,
            'x' : y,
            'name' : 'Previous results average',
            'type' : 'bar',
            'orientation' : 'v'}
        x=[]
        y=[]
        for index, row in nMetrics.iterrows():
            test = "{}-{}".format(row['profile'], row['messageSize'])
            value = "{}".format(row['throughput'])
            x.append(value)
            y.append(test)
        new = {'y' : x,
            'x' : y,
            'name' : 'Current results average',
            'type' : 'bar',
            'orientation' : 'v'}
        metrics.append(old)
        metrics.append(new)

    elif meta["benchmark"] == "ingress-perf" :
        index = "ingress-performance"
        data = await getResults(uuid,uuids,index)
    else:
        index = "ripsaw-kube-burner*"
        uuids = await getMatchRuns(meta,True)

        # We need to look at the jobSummary to ensure all UUIDs have similar iteration count.
        job = await jobSummary([uuid])
        jobs = await jobSummary(uuids)
        ids = jobFilter(job,jobs)

        oData = await getBurnerResults(uuid,ids,index)

        oMetrics = await processBurner(oData)
        oMetrics = oMetrics.reset_index()
        cData = await getBurnerResults(uuid,[uuid],index)
        nMetrics = await processBurner(cData)
        nMetrics = nMetrics.reset_index()
        x=[]
        y=[]
        for index, row in oMetrics.iterrows():
            test = "PodLatency-p99"
            value = row['P99']
            x.append(int(value)/1000)
            y.append(test)
        old = {'y' : x,
            'x' : y,
            'name' : 'Previous results p99',
            'type' : 'bar',
            'orientation' : 'v'}
        x=[]
        y=[]
        for index, row in nMetrics.iterrows():
            test = "PodLatency-p99"
            value = row['P99']
            x.append(int(value)/1000)
            y.append(test)
        new = {'y' : x,
            'x' : y,
            'name' : 'Current results P99',
            'type' : 'bar',
            'orientation' : 'v'}
        metrics.append(old)
        metrics.append(new)
    return metrics

async def jobSummary(uuids: list):
    index = "ripsaw-kube-burner*"
    ids = "\" OR uuid: \"".join(uuids)
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'( uuid: \"{ids}\" )'
                    f' AND metricName: "jobSummary"'
                    )
            }
        }
    }
    print(query)
    es = ElasticService(airflow=False,index=index)
    response = await es.post(query)
    await es.close()
    runs = [item['_source'] for item in response["hits"]["hits"]]
    return runs

async def processBurner(data: dict) :
    pprint.pprint(data)
    df = pd.json_normalize(data)
    filterDF = burnerFilter(df)
    ptile = filterDF.groupby(['quantileName'])['P99'].quantile([.99])
    return ptile

async def processNetperf(data: dict) :
    pprint.pprint(data)
    df = pd.json_normalize(data)
    filterDF = netperfFilter(df)
    tput = filterDF.groupby(['profile','messageSize'])['throughput'].mean()
    return tput

def jobFilter(pdata: dict, data: dict):
    columns = ['uuid','jobConfig.jobIterations']
    pdf = pd.json_normalize(pdata)
    pick_df = pd.DataFrame(pdf, columns=columns)
    iterations = pick_df.iloc[0]['jobConfig.jobIterations']
    df = pd.json_normalize(data)
    ndf = pd.DataFrame(df, columns=columns)
    ids_df = ndf.loc[df['jobConfig.jobIterations'] == iterations ]
    return ids_df['uuid'].to_list()

def burnerFilter(data: dict) :
    #
    # Filter out aspects of the test to norm results
    #
    pprint.pprint(data)
    columns = ['quantileName','metricName', 'P99']
    ndf = pd.DataFrame(data, columns=columns)
    print(ndf)
    return ndf

def netperfFilter(df):
    #
    # Filter out aspects of the test to norm results
    #
    columns = ['profile','hostNetwork','parallelism','service','acrossAZ','samples',
               'messageSize','throughput','test']
    ndf = pd.DataFrame(df, columns=columns)
    hnfilter = df[ (ndf.hostNetwork == True) ].index
    hnd = ndf.drop(hnfilter)
    sfilter = hnd[ (hnd.service == True)].index
    sdf = hnd.drop(sfilter)
    azfilter = sdf[ (sdf.acrossAZ == True)].index
    adf = sdf.drop(azfilter)
    d = adf[ (adf.parallelism == 1) ]
    d = d[d.profile.str.contains('TCP_STREAM')]
    return d

async def getBurnerResults(uuid: str, uuids: list, index: str ):

    if len(uuids) > 1 :
        uuids.remove(uuid)
    ids = "\" OR uuid: \"".join(uuids)
    print(ids)
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'( uuid: \"{ids}\" )'
                    f' AND metricName: "podLatencyQuantilesMeasurement"'
                    f' AND quantileName: "Ready"'
                    )
            }
        }
    }
    print(query)
    es = ElasticService(airflow=False,index=index)
    response = await es.post(query)
    await es.close()
    runs = [item['_source'] for item in response["hits"]["hits"]]
    return runs

async def getResults(uuid: str, uuids: list, index: str ):
    if len(uuids) > 1 :
        uuids.remove(uuid)
    ids = "\" OR uuid: \"".join(uuids)
    print(ids)
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'(uuid: \"{ids}\")')
            }
        }
    }
    print(query)
    es = ElasticService(airflow=False,index=index)
    response = await es.post(query)
    await es.close()
    runs = [item['_source'] for item in response["hits"]["hits"]]
    return runs

async def getMatchRuns(meta: dict, workerCount: False):
    index = "perf_scale_ci"
    version = meta["ocpVersion"][:4]
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'benchmark: "{meta["benchmark"]}"'
                    f' AND workerNodesType: "{meta["workerNodesType"]}"'
                    f' AND masterNodesType: "{meta["masterNodesType"]}"'
                    f' AND platform: "{meta["platform"]}"'
                    f' AND ocpVersion: {version}*'
                    f' AND jobStatus: success'
                    )
            }
        }
    }
    if workerCount :
        query = {
            "query": {
                "query_string": {
                    "query": (
                        f'benchmark: "{meta["benchmark"]}"'
                        f' AND workerNodesType: "{meta["workerNodesType"]}"'
                        f' AND masterNodesType: "{meta["masterNodesType"]}"'
                        f' AND masterNodesCount: "{meta["masterNodesCount"]}"'
                        f' AND workerNodesCount: "{meta["workerNodesCount"]}"'
                        f' AND platform: "{meta["platform"]}"'
                        f' AND ocpVersion: {version}*'
                        f' AND jobStatus: success'
                        )
                }
            }
        }
    print(query)
    es = ElasticService(airflow=False)
    response = await es.post(query)
    await es.close()
    runs = [item['_source'] for item in response["hits"]["hits"]]
    uuids = []
    for run in runs :
        uuids.append(run["uuid"])
    return uuids

async def getMetadata(uuid: str) :
    index = "perf_scale_ci"
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'uuid: "{uuid}"')
            }
        }
    }
    print(query)
    es = ElasticService(airflow=False)
    response = await es.post(query)
    await es.close()
    meta = [item['_source'] for item in response["hits"]["hits"]]
    return meta[0]

"""
    [ {
        'y' : ["4,13","4.14"],
        'x' : [100,120],
        'type' : 'bar',
        'orientation' : 'v'
    }]
"""
