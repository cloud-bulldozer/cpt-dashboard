import os
import typing

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import orjson

from app.api.api import router


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content)


ORIGINS_DEV = ["http://localhost:3000", "localhost:3000"]


def parse_origins(origins: typing.Optional[str]) -> list[str]:
    """Parse a comma delimited list of allowed URL Origins."""
    if not origins:
        return ORIGINS_DEV.copy()
    return [
        raw.strip().rstrip("/")  # strip whitespace and trailing slash
        for raw in origins.split(",")
        if raw.strip()  # filter out empty strings
    ] + ORIGINS_DEV


origins = parse_origins(os.getenv("CORS_ALLOWED_ORIGINS"))

app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url=None,
    title="CPT-Dashboard API Documentation",
    version="0.0.1",
    contact={
        "name": "OCP PerfScale Jedi",
        "url": "https://redhat.enterprise.slack.com/archives/C05CDC19ZKJ",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routes_to_reroute = ["/"]


@app.middleware("http")
async def some_middleware(request: Request, call_next):
    if request.url.path in routes_to_reroute:
        request.scope["path"] = "/docs"
        headers = dict(request.scope["headers"])
        headers[b"custom-header"] = b"my custom header"
        request.scope["headers"] = [(k, v) for k, v in headers.items()]
    return await call_next(request)


app.include_router(router)
