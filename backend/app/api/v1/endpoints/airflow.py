import json
from datetime import datetime,timedelta
import trio
import semver
from fastapi import APIRouter, Response

from app.models.airflow import Dag, DagRun
from app.core import airflow_transform
from app.services.airflow import AirflowService
from app.async_util import trio_run_with_asyncio
from .common import getData

router = APIRouter()
airflow_service = AirflowService()


@router.post('/api/v1/vairflow')
@router.get('/api/v1/vairflow')
async def airflow(pretty: bool = False):
    response = await getData("AIRFLOW", True)
    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')
    return response
    # path = "api/v1/dags"
    # response = await airflow_service.async_get(path)
    # dags = await trio_run_with_asyncio(trio_main, response['dags'])
    # return airflow_transform.build_airflow_dataframe(dags)



@router.post('/api/v1/vactive')
@router.get('/api/v1/vactive')
async def airflow_active(pretty: bool = False):
    path = "api/v1/dags"
    results = []
    response = await airflow_service.async_get(path)
    for dag in response['dags'] :
        if dag['is_paused'] :
            continue
        else :
            results.append(dag)
    if pretty:
        json_str = json.dumps(results, indent=4)
        return Response(content=json_str, media_type='application/json')
    return results


async def trio_main(dags):
    results = []

    async def make_dag(s, dag_data):
        print(dag_data['dag_id'])
        if parse_id(dag_data['dag_id']) is None or get_release_stream(dag_data['tags']) is None :
            return
        dag = Dag(
            **dag_data,
            **parse_id(dag_data['dag_id']),
            **get_release_stream(dag_data['tags']))
        if dag.profile == "sdn" :
            return
        r = await get_runs(s, dag.dag_id)
        # Skip dags w/o runs
        if len(r['dag_runs']) == 0:
            return
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
    # Find the dags from the last 60 days
    date = (datetime.now()-timedelta(days=60)).strftime("%Y-%m-%dT00:00:00Z")
    path = (
        f"{airflow_service.base_url}/"
        f"api/v1/dags/{dag_id}"
        f"/dagRuns?limit=10&execution_date_gte={date}")
    r = await s.get(path)
    r.raise_for_status()
    return r.json()


def parse_id(dag_id: str):
    return dict(zip(('version', 'platform', 'profile'), dag_id.split('-')))

def get_release_stream(tags: list):
    for tag in tags:
        if "-stable" in tag['name'] or semver.VersionInfo.isvalid(tag['name']):
            return {"release_stream": tag['name']}
