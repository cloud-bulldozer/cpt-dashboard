import trio
import semver
from fastapi import APIRouter

from app.models.airflow import Dag, DagRun
from app.core import airflow_transform
from app.services.airflow import AirflowService
from app.async_util import trio_run_with_asyncio

router = APIRouter()
airflow_service = AirflowService()


@router.post('/api/airflow')
@router.get('/api/airflow')
async def airflow():
    path = "api/v1/dags"
    response = await airflow_service.async_get(path)
    dags = await trio_run_with_asyncio(trio_main, response['dags'])
    return airflow_transform.build_airflow_dataframe(dags)


async def trio_main(dags):
    results = []

    async def make_dag(s, dag_data):
        dag = Dag(
            **dag_data,
            **parse_id(dag_data['dag_id']),
            **get_release_stream(dag_data['tags']))
        r = await get_runs(s, dag.dag_id)
        dag.runs = [DagRun(**run).dict() for run in r['dag_runs']]
        results.append(dag.dict())

    async with airflow_service.httpx_client() as session:
        async with trio.open_nursery() as n:
            for dag in dags:
                n.start_soon(
                    make_dag,
                    session,
                    dag
                )

    return results


async def get_runs(s, dag_id):
    path = (
        f"{airflow_service.base_url}/"
        f"api/v1/dags/{dag_id}"
        f"/dagRuns?limit=10&execution_date_gte=2021-04-18T15%3A40%3A39")
    r = await s.get(path)
    r.raise_for_status()
    return r.json()


def parse_id(dag_id: str):
    return dict(zip(('version', 'platform', 'profile'), dag_id.split('_')))


def get_release_stream(tags: list):
    for tag in tags:
        if "-stable" in tag['name'] or semver.VersionInfo.isvalid(tag['name']):
            return {"release_stream": tag['name']}
