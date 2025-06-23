from typing import Annotated

from fastapi import APIRouter, Path, Request, Response

from app.services.horreum_svc import HorreumService

router = APIRouter()


@router.get("/api/v1/horreum/api/{path:path}")
async def horreum(
    request: Request, path: Annotated[str, Path(title="Horreum API path")]
) -> Response:
    """Pass GET API call to Horreum

    Makes an authenticated Horreum call using the configured Horreum URL,
    username, and password. It passes on the query parameters as well as the
    Horreum API path, and returns the status, content, and response headers
    to the caller.

    Args:
        request: Tells FastAPI to show us the full request object
        path: A Horreum API path, like /api/test/byName/name
    """
    response = HorreumService("horreum").get(path, dict(request.query_params.items()))
    return Response(
        status_code=response.status_code,
        headers=response.headers,
        content=response.content,
    )
