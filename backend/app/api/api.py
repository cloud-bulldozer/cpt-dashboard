import sys
from fastapi import APIRouter

from app.api.v1.endpoints.ocp import results
from app.api.v1.endpoints.ocp import ocpJobs
from app.api.v1.endpoints.ocp import graph
from app.api.v1.endpoints.cpt import cptJobs
from app.api.v1.endpoints.jira import jira
from app.api.v1.endpoints.horreum import horreum
from app.api.v1.endpoints.quay import quayJobs
from app.api.v1.endpoints.quay import quayGraphs
from app.api.v1.endpoints.telco import telcoJobs
from app.api.v1.endpoints.telco import telcoGraphs
from app.api.v1.endpoints.ocm import ocmJobs
from app.api.v1.endpoints.ilab import ilab


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

# Telco endpoints
router.include_router(telcoJobs.router, tags=['telco'])
router.include_router(telcoGraphs.router, tags=['telco'])

# Jira endpoints
router.include_router(jira.router, tags=['jira'])

# Horreum endpoint
router.include_router(horreum.router, tags=['horreum'])

# OCM endpoint
router.include_router(ocmJobs.router, tags=['ocm'])

# InstructLab endpoint
router.include_router(router=ilab.router, tags=['ilab'])
