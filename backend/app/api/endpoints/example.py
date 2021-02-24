import time

import httpx
from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.get('/now')
async def now():
    return {'time': time.time()}


@router.get("/")
def root(request: Request):
    return {
        "url": str(request.url),
        "root_path": request.scope.get('root_path')
    }


@router.get("/domain/{domain}")
async def get_domain(domain: str):
    async with httpx.AsyncClient() as client:
        resp: Response = await client.get(f"http://ip-api.com/json/{domain}")
        resp.raise_for_status()
    return resp.json()
