import asyncio
from datetime import datetime
from pprint import pprint

import trio
from fastapi import APIRouter

from app.services.airflow import AirflowService
from app.services.search import ElasticService

router = APIRouter()

airflow_service = AirflowService()


async def trio_main(tasks):
    results = {}

    async def grabber(s, upstream_job, upstream_job_build, build_tag):
        r = await s.get(
            (f"{airflow_service.base_url}/api/v1"
            f"/dags/{upstream_job}"
            f"/dagRuns/{upstream_job_build}"
            f"/taskInstances/{build_tag}"))
        t = r.json()
        results[build_tag] = t['state']

    async with airflow_service.httpx_client() as session:
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


async def asyncio_main(trio_fn, task_list):
    # print(task_list)

    asyncio_loop = asyncio.get_running_loop()

    def run_sync_soon_threadsafe(fn):
        asyncio_loop.call_soon_threadsafe(fn)

    done_fut = asyncio.Future()

    def done_callback(trio_main_outcome):
        done_fut.set_result(trio_main_outcome)

    trio.lowlevel.start_guest_run(
        trio_fn, task_list,
        run_sync_soon_threadsafe=run_sync_soon_threadsafe,
        done_callback=done_callback,
        host_uses_signal_set_wakeup_fd=True
    )
    trio_main_outcome = await done_fut
    return trio_main_outcome.unwrap()


def get_tasks_states(upstream_job, upstream_job_build, tasks):
    results = {}
    for task in tasks:
        path = (f"api/v1"
             f"/dags/{upstream_job}"
             f"/dagRuns/{upstream_job_build}"
             f"/taskInstances/{task['build_tag']}")
        # print(path)
        r = airflow_service.get(path)
        # print(r)
        results[task['build_tag']] = r['state']
    return results


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

    now = datetime.now()
    tasks_states = await asyncio_main(trio_main, tasks)
    # tasks_states = get_tasks_states(pipeline_id, job_id, tasks)
    later = datetime.now()
    print(f"we got: {tasks_states}")
    print(f"latency: {later - now}")

    for task in tasks:
        task['job_status'] = tasks_states[task['build_tag']]

    return tasks
