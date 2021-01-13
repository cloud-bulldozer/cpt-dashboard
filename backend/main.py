import time

import httpx
from httpx import Response
from fastapi import FastAPI, Request
import orjson

from services import transform


app = FastAPI()


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
async def wide():
    transform.to_ocpapp_tst('tests/mocklong.csv', 'tests/widened2.json')
    with open('tests/widened2.json', 'r') as wjson:
        return orjson.loads(wjson.read())
