from fastapi import APIRouter

from app.api.v1.endpoints import results
from app.api.v1.endpoints import jobs
from app.api.v1.endpoints import graph

ocp = APIRouter()

# OCP endopoints
ocp.include_router(jobs.router, tags=['jobs'])
ocp.include_router(results.router, tags=['jobs'])
ocp.include_router(graph.router, tags=['graphs'])
