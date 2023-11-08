from fastapi import APIRouter

from app.api.v1.endpoints import results
from app.api.v1.endpoints import jobs
from app.api.v1.endpoints import graph

ocm = APIRouter()

# OCM endopoints
ocm.include_router(jobs.router, tags=['jobs'])
ocm.include_router(results.router, tags=['jobs'])
ocm.include_router(graph.router, tags=['graphs'])
