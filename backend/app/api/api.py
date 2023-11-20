from fastapi import APIRouter

from app.api.v1.endpoints.ocp import results
from app.api.v1.endpoints.ocp import ocpJobs
from app.api.v1.endpoints.ocp import graph
from app.api.v1.endpoints.cpt import cptJobs

router = APIRouter()

# OCP endopoints
router.include_router(ocpJobs.router, tags=['ocp'])
router.include_router(results.router, tags=['ocp'])
router.include_router(graph.router, tags=['ocp.graphs'])

# CPT endopoints
router.include_router(cptJobs.router, tags=['cpt'])