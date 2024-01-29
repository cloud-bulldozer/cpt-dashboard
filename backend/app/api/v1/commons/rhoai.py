from datetime import date
import pandas as pd
from app.services.search import ElasticService


import asyncio
import typing


def return_awaited_value(coroutine: asyncio.coroutines) -> typing.Any:

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(coroutine)
    return result


async def getData(start_datetime: date, end_datetime: date, configpath: str):
    query = {
        "timeout": "300s",
        "query": {
            "bool": {
                "filter": {
                    "range": {
                        "metadata.start": {
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
        }
    }
    query['query']['bool']['filter']['range']['metadata.start']['lte'] = str(end_datetime)
    query['query']['bool']['filter']['range']['metadata.start']['gte'] = str(start_datetime)

    es = ElasticService(configpath=configpath)

    response = await es.post(query)
    await es.close()

    tasks = [item['_source'] for item in response["hits"]["hits"]]
    jobs = pd.json_normalize(tasks)

    if len(jobs) == 0:
        return jobs

    return jobs
