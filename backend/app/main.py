import time
import typing

import httpx
from httpx import Response
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import orjson
from pydantic import BaseModel

from app.services import transform
from app.api.elasticsearch_api import Elasticsearch_API


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content)


class Timesrange(BaseModel):
    format: str
    gte: str
    lte: str


class Timestamp(BaseModel):
    timestamp: Timesrange


class Range(BaseModel):
    range: Timestamp


class Query(BaseModel):
    query: Range


origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app = FastAPI(default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root(request: Request):
    return {
        "url": str(request.url),
        "root_path": request.scope.get('root_path')
    }


@app.get("/domain/{domain}")
async def get_domain(domain: str):
    async with httpx.AsyncClient() as client:
        resp: Response = await client.get(f"http://ip-api.com/json/{domain}")
        resp.raise_for_status()
    return resp.json()


@app.get('/time')
async def now():
    return {'time': time.time()}


@app.get('/api/widened')
def wide():
    transform.to_ocpapp_tst('tests/mocklong.csv', 'tests/widened2.json')
    with open('tests/widened2.json', 'r') as wjson:
        return orjson.loads(wjson.read())


# add default query
@app.post('/api/download')
def download(query: Query = Query(
    query = {
        'range': {
            'timestamp': {
                'format': 'strict_date_optional_time',
                'gte': 'now-3M',
                'lte': 'now'
            }
        }
    })
):
    es = Elasticsearch_API()
    response = {}

    # try:
    # first get the es response
    response = es.post(query)

    # print(response)
    # except:
    #     print("Elasticsearch post failed")

    # try:
    #     # parse the response
    #     response = transform.to_ocpapp(response)
    #     print(response)
    # except:
    #     print("Error parsing Elasticsearch response")
    # print(response)

    response = transform.to_ocpapp(response)
    # print(response)
    return response

    # transform.to_ocpapp_tst('./app/tests/mocklong2.csv', './app/tests/tab_wide.json')
    # with open('./app/tests/tab_wide.json') as wide:
        # d = wide.read()
        # print(d)
        
    # return orjson.loads(d)
