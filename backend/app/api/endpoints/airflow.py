from fastapi import APIRouter

import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from app.models.airflow import Dag, DagRun
import semver
from app.core import airflow_transform
from app.services.airflow import AirflowService

router = APIRouter()
airflow_service = AirflowService()

from datetime import datetime
import asyncio
import trio


# @router.post('/api/airflow')
# @router.get('/api/airflow')
# def airflow():
#     path = "api/v1/dags"
#     response = airflow_service.get(path)
#     parsed_dags = [
#         {**dag, **parse_id(dag['dag_id']), **get_release_stream(dag['tags'])}
#         for dag in response['dags']]
#     dags = [Dag(**dag) for dag in parsed_dags]
#     now = datetime.now()
#     for dag in dags:
#         dag.runs = get_runs(dag.dag_id)
#     later = datetime.now()
#     # print(f"we got: {dags}")
#     print(f"latency: {later - now}")
#     dags = [dag.dict() for dag in dags]
#     return airflow_transform.build_airflow_dataframe(dags)


async def trio_main(dags):
    results = []

    async def grabber(s, dag):
        path = (
            f"{airflow_service.base_url}/"
            f"api/v1/dags/{dag.dag_id}"
            f"/dagRuns?limit=10&execution_date_gte=2021-04-18T15%3A40%3A39")
        r = await s.get(path)
        r2 = r.json()
        dag.runs = [DagRun(**run).dict() for run in r2['dag_runs']]
        results.append(dag)

    async with airflow_service.httpx_client() as session:
        async with trio.open_nursery() as n:
            for dag in dags:
                n.start_soon(
                    grabber,
                    session,
                    dag
                )

    return results


@router.post('/api/airflow')
@router.get('/api/airflow')
async def airflow():
    path = "api/v1/dags"
    response = airflow_service.get(path)
    parsed_dags = [
        {**dag, **parse_id(dag['dag_id']), **get_release_stream(dag['tags'])}
        for dag in response['dags']]
    dags = [Dag(**dag) for dag in parsed_dags]

    now = datetime.now()
    # get dag runs
    dags = await asyncio_main(trio_main, dags)
    later = datetime.now()
    # print(f"we got: {dags}")
    print(f"latency: {later - now}")

    dags = [dag.dict() for dag in dags]
    return airflow_transform.build_airflow_dataframe(dags)


def parse_id(dag_id: str):
    return dict(zip(('version', 'platform', 'profile'), dag_id.split('_')))


def get_release_stream(tags: list):
    for tag in tags:
        if "-stable" in tag['name'] or semver.VersionInfo.isvalid(tag['name']):
            return {"release_stream": tag['name']}


async def async_get_runs(dag_id: str):
    path = (
        f"api/v1/dags/{dag_id}"
        f"/dagRuns?limit=10&execution_date_gte=2021-04-18T15%3A40%3A39")
    response = airflow_service.get(path)

    return [DagRun(**run).dict() for run in response['dag_runs']]


def get_runs(dag_id: str):
    path = (
        f"api/v1/dags/{dag_id}"
        f"/dagRuns?limit=10&execution_date_gte=2021-04-18T15%3A40%3A39")
    response = airflow_service.get(path)
    return [DagRun(**run).dict() for run in response['dag_runs']]



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


