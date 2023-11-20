import asyncio
from typing import Dict, Iterable

import httpx
from fastapi import APIRouter, Request
from fastapi.param_functions import Query, Path

from app.services.search import ElasticService

router = APIRouter()

@router.get('/api/ocp/v1/jobs/{ci}/{job_id}',
            summary="Returns the details of a specified Job.")
async def results_for_job(
                ci: str = Path(..., description="Name of the CI system tha tthe job belongs to.", examples=["PROW", "JENKINS"]),
                job_id: str = Path(..., description="Unique identifier of the Jon, normally the UUID.", examples=["8b671d0b-8638-4423-b453-cc54b1caf529"]),
                ):
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'uuid: "{job_id}"')
            }
        }
    }

    airflow = False
    if ci == "AIRFLOW":
        airflow = True

    es = ElasticService(airflow=airflow)
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    if ci == "AIRFLOW":
        tasks_states = await async_tasks_states(tasks)

        for task in tasks:
            task['job_status'] = tasks_states[task['build_tag']]

    return tasks


async def async_tasks_states(tasks: Iterable) -> Dict[str, str]:
    async with airflow_service.httpx_client() as session:
        tasks_states = await asyncio.gather(
            *[call_url(session, task) for task in tasks]
        )
    return {
        task: state for task_state in tasks_states
        for task, state in task_state.items()
    }


async def call_url(session: httpx.AsyncClient, task) -> Dict[str, str]:
    path = (
        f"{airflow_service.base_url}/api/v1"
        f"/dags/{task['upstream_job']}"
        f"/dagRuns/{task['upstream_job_build']}"
        f"/taskInstances/{task['build_tag']}"
    )
    resp = await session.get(path)
    resp.raise_for_status()
    return {
        task['build_tag']: resp.json()['state']
    }
