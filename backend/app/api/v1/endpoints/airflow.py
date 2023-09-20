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


@router.post('/api/v1/airflow')
@router.get('/api/v1/airflow')
async def airflow(pretty: bool = False):
    response = await getData("AIRFLOW", True)
    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')
    return response


@router.post('/api/v1/active')
@router.get('/api/v1/active')
async def airflow_active(pretty: bool = False):
    response = "This API will be deprecated in the v2 version."
    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')
    return response
