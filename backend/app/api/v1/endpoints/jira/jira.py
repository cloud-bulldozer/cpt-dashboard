from fastapi import APIRouter, Query
from app.services.jira_svc import JiraService

router = APIRouter()


@router.get(
    "/api/v1/jira",
    summary="Query Jira Issues",
)
async def query(q: str = Query(None, description="Jira query language string")):
    jira = JiraService()
    return jira.jql(q)
