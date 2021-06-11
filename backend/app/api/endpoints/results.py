import asks
from fastapi import APIRouter

from app.core import elastic_transform
from app.services.search import ElasticService

from pprint import pprint


router = APIRouter()


# @router.post('/api/results')
# @router.get('/api/results')
# async def results(
#     query={
#         'query': {
#             'range': {
#                 'timestamp': {
#                     'format': 'strict_date_optional_time',
#                     'gte': 'now-3M',
#                     'lte': 'now'
#                 }
#             }
#         }
#     }
# ):
#     es = ElasticService()
#     response = await es.post(query)
#     await es.close()
#     return elastic_transform.build_results_dataframe(response)

from app.services.airflow import AirflowService
airflow_service = AirflowService()


import trio


async def trio_main(tasks):

    session = airflow_service.asks_client()
    # results = []
    results = {}

    async def grabber(s, upstream_job, upstream_job_build, build_tag):
        # pprint((
        #     f"{airflow_service.base_url}/api/v1"
        #     f"/dags/{upstream_job}"
        #     f"/dagRuns/{upstream_job_build}"
        #     f"/tasksInstances/{build_tag}"
        # ))

        r = await s.get((
            f"{airflow_service.base_url}/api/v1"
            f"/dags/{upstream_job}"
            f"/dagRuns/{upstream_job_build}"
            f"/taskInstances/{build_tag}"),
            auth=asks.BasicAuth(
                (airflow_service.user, airflow_service.password))
        )
        t = r.json()
        # results.append(
        #     dict(
        #         pipeline_id=t['dag_id'], job_id=upstream_job_build,
        #         task_id=build_tag, state=t['state']
        #     )
        # )
        # results |= dict(build_tag=build_tag, job_status=t['state'])
        results[build_tag] = t['state']


    async with trio.open_nursery() as n:
        for task in tasks:
            n.start_soon(
                grabber,
                session,
                task['upstream_job'],
                task['upstream_job_build'],
                task['build_tag']
            )

    return results




import inspect

import asyncio


async def asyncio_main(task_list):
    # print(task_list)

    asyncio_loop = asyncio.get_running_loop()

    def run_sync_soon_threadsafe(fn):
        asyncio_loop.call_soon_threadsafe(fn)

    done_fut = asyncio.Future()
    def done_callback(trio_main_outcome):
        # print(f"trio program ended with: {trio_main_outcome}")
        done_fut.set_result(trio_main_outcome)

        return trio_main_outcome

    trio.lowlevel.start_guest_run(
        trio_main, task_list,
        run_sync_soon_threadsafe=run_sync_soon_threadsafe,
        done_callback=done_callback,
        host_uses_signal_set_wakeup_fd=True
    )
    trio_main_outcome = await done_fut
    # print(inspect.getmembers(trio_main_outcome))
    return trio_main_outcome.unwrap()





@router.get('/api/results/{pipeline_id}/{job_id}')
async def results_for_job(pipeline_id: str, job_id: str):
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'upstream_job: "{pipeline_id}" '
                    f'AND upstream_job_build: "{job_id}"')
            }
        }
    }

    es = ElasticService()
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]

    tasks_states = await asyncio_main(tasks)
    print(f"we got: {tasks_states}")

    # for task in tasks:
    #     task['job_status'] = tasks_states[task['build_tag']]

    pprint([dict(build_tag=t['build_tag'], job_status=t['job_status']) for t in tasks])
    pprint(tasks_states)
    return tasks
