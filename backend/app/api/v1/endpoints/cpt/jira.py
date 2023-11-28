from fastapi import Response, APIRouter, Query
from app.services.jira_svc import JiraService

router = APIRouter()

@router.get(
    '/api/cpt/v1/jira',
    summary="Query Jira Issues",
)
async def query(
        q: Query = Query(None, description="Jira query language string")
):
    jira = JiraService()
    return jira.jql(q)
