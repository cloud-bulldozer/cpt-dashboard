from fastapi import APIRouter

from app.api.v1.endpoints import results
from app.api.v1.endpoints import airflow
from app.api.v1.endpoints import jobs
from app.api.v1.endpoints import jenkins
from app.api.v1.endpoints import graph
from app.api.v2.endpoints import jobs as jobsv2

api_router = APIRouter()

# v1 endopoints
api_router.include_router(results.router, tags=['perfscale'])
api_router.include_router(airflow.router, tags=['perfscale'])
api_router.include_router(jobs.router, tags=['perfscale'])
api_router.include_router(jenkins.router, tags=['perfscale'])
api_router.include_router(graph.router, tags=['perfscale'])

# v2 endpoints
api_router.include_router(jobsv2.router, tags=['perfscale', 'v2'])
