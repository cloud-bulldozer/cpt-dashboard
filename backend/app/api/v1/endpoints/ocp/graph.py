from datetime import datetime, timedelta
from app.api.v1.commons.utils import getMetadata
import trio
import semver
from fastapi import APIRouter
import io
import pprint
from json import loads
import pandas as pd
from app.services.search import ElasticService

router = APIRouter()

"""
"""


@router.get("/api/v1/ocp/graph/trend/{version}/{count}/{benchmark}")
async def trend(benchmark: str, count: int, version: str):
    index = "ripsaw-kube-burner*"
    meta = {}
    meta["benchmark"] = benchmark
    # Instance types for self-managed.
    if count > 50:
        meta["masterNodesType"] = "m6a.4xlarge"
        meta["workerNodesType"] = "m5.xlarge"
    else:
        meta["masterNodesType"] = "m6a.xlarge"
        meta["workerNodesType"] = "m6a.xlarge"
    meta["masterNodesCount"] = 3
    meta["workerNodesCount"] = count
    meta["platform"] = "AWS"
    # Query the up coming release data
    meta["ocpVersion"] = version
    current_uuids = await getMatchRuns(meta, True)
    if len(current_uuids) < 1:
        return []

    current_jobs = await jobSummary(current_uuids)
    current_ids = jobFilter(current_jobs, current_jobs)
    # Capture result data
    oData = await getBurnerResults("", current_ids, index)
    odf = pd.json_normalize(oData)
    columns = ["timestamp", "quantileName", "metricName", "P99"]
    odf = pd.DataFrame(odf, columns=columns)
    odf = odf.sort_values(by=["timestamp"])
    current = {
        "y": (odf["P99"] / 1000).to_list(),
        "x": odf["timestamp"].to_list(),
        "name": version + " results - PodLatency: Ready 99th%tile ( seconds )",
        "type": "scatter",
    }
    return [current]


"""
diff_cpu - Will accept the version, prev_version , count, benchmark and namespace to diff trend CPU
data.
"""


@router.get(
    "/api/v1/ocp/graph/trend/{version}/{prev_version}/{count}/{benchmark}/cpu/{namespace}"
)
async def diff_cpu(
    namespace: str, benchmark: str, count: int, version: str, prev_version: str
):
    aTrend = await trend_cpu(namespace, benchmark, count, version)
    bTrend = await trend_cpu(namespace, benchmark, count, prev_version)
    return [aTrend[0], bTrend[0]]


"""
trend_cpu - Will accept the version, count, benchmark and namespace to trend CPU
data.
"""


@router.get("/api/v1/ocp/graph/trend/{version}/{count}/{benchmark}/cpu/{namespace}")
async def trend_cpu(namespace: str, benchmark: str, count: int, version: str):
    index = "ripsaw-kube-burner*"
    meta = {}
    meta["benchmark"] = benchmark
    meta["masterNodesCount"] = 3
    # Instance types for self-managed.
    if count > 50:
        meta["masterNodesType"] = "m6a.4xlarge"
        meta["workerNodesType"] = "m5.xlarge"
    elif count <= 24 and count > 20:
        meta["masterNodesType"] = "m6a.xlarge"
        meta["workerNodesType"] = "m6a.xlarge"
    else:
        meta["masterNodesType"] = "m5.2large"
        meta["workerNodesType"] = "m5.xlarge"
    meta["workerNodesCount"] = count
    meta["platform"] = "AWS"
    meta["ocpVersion"] = version
    current_uuids = await getMatchRuns(meta, True)
    # Query the current release data.
    current_jobs = await jobSummary(current_uuids)
    current_ids = jobFilter(current_jobs, current_jobs)
    result = await getBurnerCPUResults(current_ids, namespace, index)
    result = parseCPUResults(result)
    cdf = pd.json_normalize(result)
    cdf = cdf.sort_values(by=["timestamp"])
    current = {
        "y": cdf["cpu_avg"].to_list(),
        "x": cdf["timestamp"].to_list(),
        "name": version
        + " results - "
        + namespace
        + " avg CPU usage - for benchmark "
        + benchmark,
        "type": "scatter",
    }

    return [current]


def parseCPUResults(data: dict):
    res = []
    stamps = data["aggregations"]["time"]["buckets"]
    cpu = data["aggregations"]["uuid"]["buckets"]
    for stamp in stamps:
        dat = {}
        dat["uuid"] = stamp["key"]
        dat["timestamp"] = stamp["time"]["value_as_string"]
        acpu = next(item for item in cpu if item["key"] == stamp["key"])
        dat["cpu_avg"] = acpu["cpu"]["value"]
        res.append(dat)
    return res


@router.get("/api/v1/ocp/graph/{uuid}")
async def graph(uuid: str):
    index = ""
    meta = await getMetadata(uuid, "ocp.elasticsearch")
    print(meta)
    metrics = []
    if meta["benchmark"] == "k8s-netperf":
        uuids = await getMatchRuns(meta, False)
        print(uuids)
        index = "k8s-netperf"
        oData = await getResults(uuid, uuids, index)
        cData = await getResults(uuid, [uuid], index)
        oMetrics = await processNetperf(oData)
        oMetrics = oMetrics.reset_index()
        nMetrics = await processNetperf(cData)
        nMetrics = nMetrics.reset_index()
        x = []
        y = []
        for index, row in oMetrics.iterrows():
            test = "{}-{}".format(row["profile"], row["messageSize"])
            value = "{}".format(row["throughput"])
            x.append(value)
            y.append(test)
        old = {
            "y": x,
            "x": y,
            "name": "Previous results average",
            "type": "bar",
            "orientation": "v",
        }
        x = []
        y = []
        for index, row in nMetrics.iterrows():
            test = "{}-{}".format(row["profile"], row["messageSize"])
            value = "{}".format(row["throughput"])
            x.append(value)
            y.append(test)
        new = {
            "y": x,
            "x": y,
            "name": "Current results average",
            "type": "bar",
            "orientation": "v",
        }
        metrics.append(old)
        metrics.append(new)

    elif meta["benchmark"] == "ingress-perf":
        uuids = await getMatchRuns(meta, False)
        index = "ingress-performance"
        data = await getResults(uuid, uuids, index)
    else:
        index = "ripsaw-kube-burner*"
        uuids = await getMatchRuns(meta, True)

        # We need to look at the jobSummary to ensure all UUIDs have similar iteration count.
        job = await jobSummary([uuid])
        jobs = await jobSummary(uuids)
        ids = jobFilter(job, jobs)

        oData = await getBurnerResults(uuid, ids, index)
        oMetrics = await processBurner(oData)
        oMetrics = oMetrics.reset_index()

        cData = await getBurnerResults(uuid, [uuid], index)
        nMetrics = await processBurner(cData)
        nMetrics = nMetrics.reset_index()
        x = []
        y = []
        for index, row in oMetrics.iterrows():
            test = "PodLatency-p99"
            value = row["P99"]
            x.append(int(value) / 1000)
            y.append(test)
        old = {
            "y": x,
            "x": y,
            "name": "Previous results p99",
            "type": "bar",
            "orientation": "v",
        }
        x = []
        y = []
        for index, row in nMetrics.iterrows():
            test = "PodLatency-p99"
            value = row["P99"]
            x.append(int(value) / 1000)
            y.append(test)
        new = {
            "y": x,
            "x": y,
            "name": "Current results P99",
            "type": "bar",
            "orientation": "v",
        }
        metrics.append(old)
        metrics.append(new)
    return metrics


async def jobSummary(uuids: list):
    index = "ripsaw-kube-burner*"
    ids = '" OR uuid: "'.join(uuids)
    query = {
        "query": {
            "query_string": {
                "query": (f'( uuid: "{ids}" )' f' AND metricName: "jobSummary"')
            }
        }
    }
    print(query)
    es = ElasticService(configpath="ocp.elasticsearch", index=index)
    response = await es.post(query=query)
    await es.close()
    runs = [item["_source"] for item in response["data"]]
    return runs


async def processBurner(data: dict):
    pprint.pprint(data)
    df = pd.json_normalize(data)
    filterDF = burnerFilter(df)
    ptile = filterDF.groupby(["quantileName"])["P99"].quantile([0.99])
    return ptile


async def processNetperf(data: dict):
    pprint.pprint(data)
    df = pd.json_normalize(data)
    filterDF = netperfFilter(df)
    tput = filterDF.groupby(["profile", "messageSize"])["throughput"].mean()
    return tput


def jobFilter(pdata: dict, data: dict):
    columns = ["uuid", "jobConfig.jobIterations"]
    pdf = pd.json_normalize(pdata)
    pick_df = pd.DataFrame(pdf, columns=columns)
    iterations = pick_df.iloc[0]["jobConfig.jobIterations"]
    df = pd.json_normalize(data)
    ndf = pd.DataFrame(df, columns=columns)
    ids_df = ndf.loc[df["jobConfig.jobIterations"] == iterations]
    return ids_df["uuid"].to_list()


def burnerFilter(data: dict):
    #
    # Filter out aspects of the test to norm results
    #
    pprint.pprint(data)
    columns = ["quantileName", "metricName", "P99"]
    ndf = pd.DataFrame(data, columns=columns)
    return ndf


def netperfFilter(df):
    #
    # Filter out aspects of the test to norm results
    #
    columns = [
        "profile",
        "hostNetwork",
        "parallelism",
        "service",
        "acrossAZ",
        "samples",
        "messageSize",
        "throughput",
        "test",
    ]
    ndf = pd.DataFrame(df, columns=columns)
    hnfilter = df[(ndf.hostNetwork == True)].index
    hnd = ndf.drop(hnfilter)
    sfilter = hnd[(hnd.service == True)].index
    sdf = hnd.drop(sfilter)
    azfilter = sdf[(sdf.acrossAZ == True)].index
    adf = sdf.drop(azfilter)
    d = adf[(adf.parallelism == 1)]
    d = d[d.profile.str.contains("TCP_STREAM")]
    return d


async def getBurnerCPUResults(uuids: list, namespace: str, index: str):
    ids = '" OR uuid: "'.join(uuids)
    print(ids)
    query = {
        "size": 0,
        "aggs": {
            "time": {
                "terms": {"field": "uuid.keyword"},
                "aggs": {"time": {"avg": {"field": "timestamp"}}},
            },
            "uuid": {
                "terms": {"field": "uuid.keyword"},
                "aggs": {"cpu": {"avg": {"field": "value"}}},
            },
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": (
                                f'( uuid: "{ids}" )'
                                f' AND metricName: "containerCPU"'
                                f" AND labels.namespace.keyword: {namespace}"
                            )
                        }
                    }
                ]
            }
        },
    }
    print(query)
    es = ElasticService(configpath="ocp.elasticsearch", index=index)
    runs = await es.post(query, size=0)
    await es.close()
    return runs


async def getBurnerResults(uuid: str, uuids: list, index: str):
    if len(uuids) > 1:
        if len(uuid) > 0:
            uuids.remove(uuid)
    if len(uuids) < 1:
        return []
    ids = '" OR uuid: "'.join(uuids)
    print(ids)
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'( uuid: "{ids}" )'
                    f' AND metricName: "podLatencyQuantilesMeasurement"'
                    f' AND quantileName: "Ready"'
                )
            }
        }
    }
    print(query)
    es = ElasticService(configpath="ocp.elasticsearch", index=index)
    response = await es.post(query=query)
    await es.close()
    runs = [item["_source"] for item in response["data"]]
    return runs


async def getResults(uuid: str, uuids: list, index: str):
    if len(uuids) > 1:
        uuids.remove(uuid)
    ids = '" OR uuid: "'.join(uuids)
    print(ids)
    query = {"query": {"query_string": {"query": (f'(uuid: "{ids}")')}}}
    print(query)
    es = ElasticService(configpath="ocp.elasticsearch", index=index)
    response = await es.post(query=query)
    await es.close()
    runs = [item["_source"] for item in response["data"]]
    return runs


async def getMatchRuns(meta: dict, workerCount: False):
    index = "perf_scale_ci"
    version = meta["ocpVersion"][:4]
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": (
                                f'benchmark: "{meta["benchmark"]}$"'
                                f' AND workerNodesType: "{meta["workerNodesType"]}"'
                                f' AND masterNodesType: "{meta["masterNodesType"]}"'
                                f' AND platform: "{meta["platform"]}"'
                                f" AND ocpVersion: {version}*"
                                f" AND jobStatus: success"
                            )
                        }
                    }
                ]
            }
        }
    }
    if workerCount:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": (
                                    f'benchmark: "{meta["benchmark"]}$"'
                                    f' AND workerNodesType: "{meta["workerNodesType"]}"'
                                    f' AND masterNodesType: "{meta["masterNodesType"]}"'
                                    f' AND masterNodesCount: "{meta["masterNodesCount"]}"'
                                    f' AND workerNodesCount: "{meta["workerNodesCount"]}"'
                                    f' AND platform: "{meta["platform"]}"'
                                    f" AND ocpVersion: {version}*"
                                    f" AND jobStatus: success"
                                )
                            }
                        }
                    ]
                }
            }
        }

    print(query)
    es = ElasticService(configpath="ocp.elasticsearch")
    response = await es.post(query=query)
    await es.close()
    runs = [item["_source"] for item in response["data"]]
    uuids = []
    for run in runs:
        uuids.append(run["uuid"])
    return uuids


"""
    [ {
        'y' : ["4,13","4.14"],
        'x' : [100,120],
        'type' : 'bar',
        'orientation' : 'v'
    }]
"""
