import sys
import typing

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import orjson

from app.api.api import router


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content)


origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app = FastAPI(default_response_class=ORJSONResponse,
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
              })


@app.middleware("http")
async def report_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        tb = e.__traceback__
        print(f"Unhandled exception {e.__class__.__name__}: {str(e)}")
        where = "unknown"
        while tb is not None:
            where = f"{tb.tb_frame.f_code.co_filename}:{tb.tb_lineno}"
            print(
                f"  {where} {tb.tb_frame.f_code.co_name}",
                file=sys.stderr,
            )
            tb = tb.tb_next
        return JSONResponse(
            status_code=500,
            content={"message": f"Unhandled server error at {where}: {str(e)}"},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routes_to_reroute = ['/']

@app.middleware('http')
async def some_middleware(request: Request, call_next):
    if request.url.path in routes_to_reroute:
        request.scope['path'] = '/docs'
        headers = dict(request.scope['headers'])
        headers[b'custom-header'] = b'my custom header'
        request.scope['headers'] = [(k, v) for k, v in headers.items()]
    return await call_next(request)

app.include_router(router)
