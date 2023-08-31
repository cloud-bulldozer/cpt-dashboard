from fastapi import APIRouter

from app.api.endpoints import results
from app.api.endpoints import airflow
from app.api.endpoints import jobs
from app.api.endpoints import jenkins
from app.api.endpoints import graph

api_router = APIRouter()
api_router.include_router(results.router, tags=['perfscale'])
api_router.include_router(airflow.router, tags=['perfscale'])
api_router.include_router(jobs.router, tags=['perfscale'])
api_router.include_router(jenkins.router, tags=['perfscale'])
api_router.include_router(graph.router, tags=['perfscale'])
