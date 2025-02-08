from fastapi import APIRouter
from app.api.v1.commons.utils import getMetadata
from app.services.search import ElasticService


router = APIRouter()


@router.get('/api/v1/ols/graph/{uuid}')
async def graph(uuid: str):
    latencyResults = []
    apiResults = []
    api_index = "ols-load-test-results"
    metric_names = [
        "get_readiness", "get_liveness", "post_authorized",
        "get_metrics", "get_feedback_status", "post_feedback",
        "post_query", "post_streaming_query", "post_query_with_cache",
        "post_streaming_query_with_cache"
    ]
    metadata = await getMetadata(uuid, 'ocp.elasticsearch')
    uuids = await getMatchRuns(metadata)
    if uuid in uuids:
        uuids.remove(uuid)
    previousApiData = await getApiMetrics(uuids, metric_names, api_index)
    if len(uuids) > 0:
        currentApiData = await getApiMetrics([uuid], metric_names, api_index)
    else:
        currentApiData = previousApiData
    previousLatencies, previousApiResults = await parseApiResults(previousApiData)
    currentLatencies, currentApiResults = await parseApiResults(currentApiData)
    
    prevLatenciesX, prevLatenciesY, prevApiResultsX, prevApiResultsY = [], [], [], []
    currLatenciesX, currLatenciesY, currApiResultsX, currApiResultsY = [], [], [], []
    for (plKey, plValue), (clKey, clValue), (paKey, paValue), (caKey, caValue) in zip(previousLatencies.items(), 
                                                                                      currentLatencies.items(), 
                                                                                      previousApiResults.items(), 
                                                                                      currentApiResults.items()):
        prevLatenciesX.append(plKey)
        prevApiResultsX.append(paKey)
        currLatenciesX.append(clKey)
        currApiResultsX.append(caKey)
        prevLatenciesY.append(plValue/1000)
        prevApiResultsY.append(paValue)
        currLatenciesY.append(clValue/1000)
        currApiResultsY.append(caValue)
    prevLatencies = {
        'x': prevLatenciesX,
        'y': prevLatenciesY,
        'name': 'Previous API Latencies',
        'type': 'bar',
        'orientation': 'v'
    }
    currLatencies = {
        'x': currLatenciesX,
        'y': currLatenciesY,
        'name': 'Current API Latencies',
        'type': 'bar',
        'orientation': 'v'
    }
    latencyResults.append(prevLatencies)
    latencyResults.append(currLatencies)

    prevApiResults = {
        'x': prevApiResultsX,
        'y': prevApiResultsY,
        'name': 'Previous API Throughput',
        'type': 'bar',
        'orientation': 'v'
    }
    currApiResults = {
        'x': currApiResultsX,
        'y': currApiResultsY,
        'name': 'Current API Throughput',
        'type': 'bar',
        'orientation': 'v'
    }
    apiResults.append(prevApiResults)
    apiResults.append(currApiResults)

    return {
        'latencyResults': latencyResults,
        'apiResults': apiResults
    }

async def parseApiResults(apiData: dict):
    latencies, apiResults = dict(), dict()
    for each in apiData['aggregations']['group_by_metric']['buckets']:
        latencies[each['key']] = each['avg_p99Latency']['value']
        apiResults[each['key']] = each['avg_statuscode_200']['value']
    return latencies, apiResults


async def getApiMetrics(uuids: list, metric_names: list, index: str):
    query = {
       "query": {
            "bool": {
                "filter": [
                    {
                        "terms": {
                            "uuid.keyword": uuids
                        }
                    },
                    {
                        "terms": {
                            "metricName.keyword": metric_names
                        }
                    }
                ]
            }
        },
        "aggs": {
            "group_by_metric": {
                "terms": {
                    "field": "metricName.keyword",
                    "size": 10000
                },
                "aggs": {
                    "avg_p99Latency": {
                        "avg": {
                            "field": "p99Latency",
                            "missing": 0
                        }
                    },
                    "avg_statuscode_200": {
                        "avg": {
                            "field": "statusCodes.200",
                            "missing": 0
                        }
                    }
                }
            }
        }
    }
    es = ElasticService(configpath="ocp.elasticsearch",index=index)
    results = await es.post(query, size=0)
    await es.close()
    return results


async def getMatchRuns(metadata: dict):
    query = {
        "query": {
            "bool": {
                "must": [{
                    "query_string": {
                "query": (
                    f'benchmark: "{metadata["benchmark"]}$"'
                    f' AND olsTestDuration: "{metadata["olsTestDuration"]}"'
                    f' AND olsTestWorkers: "{metadata["olsTestWorkers"]}"'
                    f' AND infraNodesType: "{metadata["infraNodesType"]}"'
                    f' AND workerNodesType: "{metadata["workerNodesType"]}"'
                    f' AND masterNodesType: "{metadata["masterNodesType"]}"'
                    f' AND masterNodesCount: "{metadata["masterNodesCount"]}"'
                    f' AND workerNodesCount: "{metadata["workerNodesCount"]}"'
                    f' AND infraNodesCount: "{metadata["infraNodesCount"]}"'
                    f' AND releaseStream: "{metadata["releaseStream"]}"'
                    f' AND jobStatus: success'
                    )
                }
                }]
            }
        }
    }
    es = ElasticService(configpath="ocp.elasticsearch")
    response = await es.post(query=query)
    await es.close()
    return [item['_source']['uuid'] for item in response]
