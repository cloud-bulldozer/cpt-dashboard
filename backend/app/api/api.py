import json
from pathlib import Path
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
from app.api.v1.endpoints.ols import olsJobs
from app.api.v1.endpoints.ols import olsGraphs
from app.api.v1.endpoints.ocm import ocmJobs
from app.api.v1.endpoints.ilab import ilab


router = APIRouter()

# OCP endpoints
router.include_router(ocpJobs.router, tags=["ocp"])
router.include_router(results.router, tags=["ocp"])
router.include_router(graph.router, tags=["ocp.graphs"])

# CPT endpoints
router.include_router(cptJobs.router, tags=["cpt"])

# Quay endpoints
router.include_router(quayJobs.router, tags=["quay"])
router.include_router(quayGraphs.router, tags=["quay"])

# Telco endpoints
router.include_router(telcoJobs.router, tags=["telco"])
router.include_router(telcoGraphs.router, tags=["telco"])

# OLS endpoints
router.include_router(olsJobs.router, tags=["ols"])
router.include_router(olsGraphs.router, tags=["ols"])

# Jira endpoints
router.include_router(jira.router, tags=["jira"])

# Horreum endpoint
router.include_router(horreum.router, tags=["horreum"])

# OCM endpoint
router.include_router(ocmJobs.router, tags=["ocm"])

# InstructLab endpoint
router.include_router(router=ilab.router, tags=["ilab"])


@router.get(
    "/api/version",
    summary="Get CPT aggregator version",
    description=(
        "Return information about the CPT aggregator build, "
        "including the version, the last commit SHA, "
        "the branch on which this aggregator was built, "
        "and the build date, along with a list of the 10 most recent commits"
    ),
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "version": "0.1.0",
                        "sha": "xxxxxx",
                        "branch": "main",
                        "display_version": "v0.1.0-xxxxxx (main)",
                        "date": "2025-04-16T19:36:55.179192+00:00",
                        "changes": [
                            {
                                "sha": "xyzzy",
                                "author": "Easter Bunny",
                                "email": "bunny_the@example.com",
                                "date": "2025-04-14T14:52:38-04:00",
                                "title": "Add an easter egg",
                            }
                        ],
                    },
                }
            },
        }
    },
)
async def version():
    """Return CPT aggregator version information

    A version.json file is created at build time; this API will
    fetch it, and return it. If the file doesn't exist, or can't
    be read, return a minimal placeholder rather than fail.
    """
    version = Path("version.json")
    v = {"version": "0.0.0-none", "changes": []}
    try:
        if version.is_file():
            with version.open() as vf:
                v = json.load(vf)
    except Exception as exc:
        print(f"Unable to read {str(version)}: {str(exc)!r}")
    return v
