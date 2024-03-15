from fastapi import APIRouter

from app.api.v1.endpoints.ocp import results
from app.api.v1.endpoints.ocp import ocpJobs
from app.api.v1.endpoints.ocp import graph
from app.api.v1.endpoints.cpt import cptJobs
from app.api.v1.endpoints.jira import jira
from app.api.v1.endpoints.quay import quayJobs
from app.api.v1.endpoints.quay import quayGraphs
from app.api.v1.endpoints.stub import stub

router = APIRouter()

# OCP endpoints
router.include_router(ocpJobs.router, tags=['ocp'])
router.include_router(results.router, tags=['ocp'])
router.include_router(graph.router, tags=['ocp.graphs'])

# CPT endpoints
router.include_router(cptJobs.router, tags=['cpt'])

# Quay endpoints
router.include_router(quayJobs.router, tags=['quay'])
router.include_router(quayGraphs.router, tags=['quay'])

# Jira endpoints
router.include_router(jira.router, tags=['jira'])

# Stub endopoints
router.include_router(stub.router, tags=['stub'])
