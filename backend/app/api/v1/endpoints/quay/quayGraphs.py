import json
from fastapi import Response
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from app.api.v1.commons.utils import getMetadata, safe_add
from app.services.search import ElasticService


router = APIRouter()


@router.get('/api/v1/quay/graph/{uuid}')
async def graph(uuid: str):
    apiResults = []
    imageResults = []
    latencyResults = []
    currentApiData = None
    currentImagesData = None
    api_index = "quay-vegeta-results"
    image_push_pull_index = "quay-push-pull"
    meta = await getMetadata(uuid, 'quay.elasticsearch')
    uuids = await getMatchRuns(meta)
    if uuid in uuids and len(uuids) > 1:
        uuids.remove(uuid)
        currentApiData = await getQuayMetrics([uuid], api_index)
        currentImagesData = await getImageMetrics([uuid], image_push_pull_index)
    prevApiData = await getQuayMetrics(uuids, api_index)
    prevImagesData = await getImageMetrics(uuids, image_push_pull_index)
    if currentApiData is None:
        currentApiData = prevApiData
        currentImagesData = prevImagesData
    prevApiResults = await parseApiResults(prevApiData)
    currentApiResults = await parseApiResults(currentApiData)
    prevImagesResults = await parseImageResults(prevImagesData)
    currentImagesResults = await parseImageResults(currentImagesData)

    prevX, prevY = [], []
    currX, currY = [], []
    for (pKey, pValue), (cKey, cValue) in zip(prevApiResults.items(), currentApiResults.items()):
        prevX.append(pKey)
        currX.append(cKey)
        prevY.append(pValue)
        currY.append(cValue)
    prev = {
        'x': prevX,
        'y': prevY,
        'name': 'Previous API status codes',
        'type': 'bar',
        'orientation': 'v'
    }
    curr = {
        'x': currX,
        'y': currY,
        'name': 'Current API status codes',
        'type': 'bar',
        'orientation': 'v'
    }
    apiResults.append(prev)
    apiResults.append(curr)

    prev = {
        'x': ['success_count', 'failure_count'],
        'y': [prevImagesResults['success_count'], prevImagesResults['failure_count']],
        'name': 'Previous images status count',
        'type': 'bar',
        'orientation': 'v'
    }
    curr = {
        'x': ['success_count', 'failure_count'],
        'y': [currentImagesResults['success_count'], currentImagesResults['failure_count']],
        'name': 'Current images status count',
        'type': 'bar',
        'orientation': 'v'
    }
    imageResults.append(prev)
    imageResults.append(curr)

    prev = {
        'x': ['api_latency', 'image_push_pull_latency'],
        'y': [(prevApiData['aggregations']['latency']['value'])/1000, prevImagesResults['latency'] * 1000],
        'name': 'Previous latencies',
        'type': 'bar',
        'orientation': 'v'
    }

    curr = {
        'x': ['api_latency', 'image_push_pull_latency'],
        'y': [(currentApiData['aggregations']['latency']['value'])/1000, currentImagesResults['latency'] * 1000],
        'name': 'Current latencies',
        'type': 'bar',
        'orientation': 'v'
    }
    latencyResults.append(prev)
    latencyResults.append(curr)

    return {
        'apiResults': apiResults,
        'imageResults': imageResults,
        'latencyResults': latencyResults
    }


async def parseApiResults(data: dict):
    resultData = {'status_code_0': 0.0, 'status_code_2XX': 0.0, 'status_code_4XX': 0.0, 'status_code_5XX': 0.0}
    safe_add(data['aggregations'], resultData, 'status_codes.0', 'status_code_0')
    safe_add(data['aggregations'], resultData, 'status_codes.200', 'status_code_2XX')
    safe_add(data['aggregations'], resultData, 'status_codes.201', 'status_code_2XX')
    safe_add(data['aggregations'], resultData, 'status_codes.204', 'status_code_2XX')
    safe_add(data['aggregations'], resultData, 'status_codes.400', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.401', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.403', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.404', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.405', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.408', 'status_code_4XX')
    safe_add(data['aggregations'], resultData, 'status_codes.500', 'status_code_5XX')
    safe_add(data['aggregations'], resultData, 'status_codes.502', 'status_code_5XX')
    safe_add(data['aggregations'], resultData, 'status_codes.503', 'status_code_5XX')
    safe_add(data['aggregations'], resultData, 'status_codes.504', 'status_code_5XX')
    return resultData


async def parseImageResults(data: dict):
    totals = {'latency': 0.0, 'success_count': 0.0, 'failure_count': 0.0}
    datapoints = data['aggregations']['uuid']['buckets']
    for each in datapoints:
        safe_add(each, totals, 'latency', 'latency')
        safe_add(each, totals, 'success_count', 'success_count')
        safe_add(each, totals, 'failure_count', 'failure_count')
    totals['latency'] /= len(datapoints)
    totals['success_count'] /= len(datapoints)
    totals['failure_count'] /= len(datapoints)
    return totals


async def getImageMetrics(uuids: list, index: str):
    ids = "\" OR uuid: \"".join(uuids)
    query = {
        "size": 0,
        "aggs": {
            "uuid": {
            "terms": {
                "field": "uuid.keyword"
            },
            "aggs": {
                "latency": {
                    "avg": {
                        "field": "elapsed_time"
                    }
                },
                "success_count": {
                    "sum": {
                        "field": "success_count"
                    }
                },
                "failure_count": {
                    "sum": {
                        "field": "failure_count"
                    }
                }
            }
            }
        },
        "query": {
            "bool": {
                "must": [{
                    "query_string": {
                        "query": (
                            f'( uuid: \"{ids}\" )'
                        )
                    }
                }]
            }
        }
    }
    print(query)
    es = ElasticService(configpath="quay.elasticsearch",index=index)
    results = await es.post(query,size=0)
    await es.close()
    return results


async def getQuayMetrics(uuids: list, index: str):
    ids = "\" OR uuid: \"".join(uuids)
    query = {
        "size": 0,
        "aggs": {
            "latency": {
            "avg": {
                "field": "req_latency"
            }
            },
            "status_codes.0": {
            "avg": {
                "field": "status_codes.0"
            }
            },
            "status_codes.200": {
            "avg": {
                "field": "status_codes.200"
            }
            },
            "status_codes.201": {
            "avg": {
                "field": "status_codes.201"
            }
            },
            "status_codes.204": {
            "avg": {
                "field": "status_codes.204"
            }
            },
            "status_codes.400": {
            "avg": {
                "field": "status_codes.400"
            }
            },
            "status_codes.401": {
            "avg": {
                "field": "status_codes.401"
            }
            },
            "status_codes.403": {
            "avg": {
                "field": "status_codes.403"
            }
            },
            "status_codes.404": {
            "avg": {
                "field": "status_codes.404"
            }
            },
            "status_codes.405": {
            "avg": {
                "field": "status_codes.405"
            }
            },
            "status_codes.408": {
            "avg": {
                "field": "status_codes.408"
            }
            },
            "status_codes.500": {
            "avg": {
                "field": "status_codes.500"
            }
            },
            "status_codes.502": {
            "avg": {
                "field": "status_codes.502"
            }
            },
            "status_codes.503": {
            "avg": {
                "field": "status_codes.503"
            }
            },
            "status_codes.504": {
            "avg": {
                "field": "status_codes.504"
            }
            }
        },
        "query": {
            "bool": {
                "must": [{
                    "query_string": {
                        "query": (
                            f'( uuid: \"{ids}\" )'
                        )
                    }
                }]
            }
        }
    }
    print(query)
    es = ElasticService(configpath="quay.elasticsearch",index=index)
    results = await es.post(query,size=0)
    await es.close()
    return results


async def getMatchRuns(meta: dict):
    query = {
        "query": {
            "bool": {
                "must": [{
                    "query_string": {
                "query": (
                    f'benchmark: "{meta["benchmark"]}$"'
                    f' AND hitSize: "{meta["hitSize"]}"'
                    f' AND concurrency: "{meta["concurrency"]}"'
                    f' AND imagePushPulls: "{meta["imagePushPulls"]}"'
                    f' AND workerNodesType: "{meta["workerNodesType"]}"'
                    f' AND masterNodesType: "{meta["masterNodesType"]}"'
                    f' AND masterNodesCount: "{meta["masterNodesCount"]}"'
                    f' AND workerNodesCount: "{meta["workerNodesCount"]}"'
                    f' AND releaseStream: "{meta["releaseStream"]}"'
                    f' AND jobStatus: success'
                    )
                }
                }]
            }
        }
    }

    print(query)
    es = ElasticService(configpath="quay.elasticsearch")
    response = await es.post(query=query)
    await es.close()
    runs = [item['_source'] for item in response]
    uuids = []
    for run in runs :
        uuids.append(run["uuid"])
    return uuids