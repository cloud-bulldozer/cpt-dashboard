from datetime import datetime
from pprint import pprint

import trio
from fastapi import APIRouter

from app.services.airflow import AirflowService
from app.services.search import ElasticService
from app.util import trio_run_with_asyncio

router = APIRouter()

airflow_service = AirflowService()


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

    # now = datetime.now()
    tasks_states = await trio_run_with_asyncio(trio_main, tasks)
    # tasks_states = get_tasks_states(pipeline_id, job_id, tasks)
    # later = datetime.now()
    # print(f"we got: {tasks_states}")
    # print(f"latency: {later - now}")

    for task in tasks:
        task['job_status'] = tasks_states[task['build_tag']]

    return tasks


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
