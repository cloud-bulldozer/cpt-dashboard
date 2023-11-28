from fastapi import APIRouter

from app.api.v1.endpoints.ocp import results
from app.api.v1.endpoints.ocp import ocpJobs
from app.api.v1.endpoints.ocp import graph
from app.api.v1.endpoints.cpt import cptJobs
from app.api.v1.endpoints.cpt import jira

router = APIRouter()

# OCP endopoints
router.include_router(ocpJobs.router, tags=['ocp'])
router.include_router(results.router, tags=['ocp'])
router.include_router(graph.router, tags=['ocp.graphs'])

# CPT endopoints
router.include_router(cptJobs.router, tags=['cpt'])
router.include_router(jira.router, tags=['cpt.jira'])

