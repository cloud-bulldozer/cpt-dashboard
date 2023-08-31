from .common import getData
from fastapi import APIRouter

from app.async_util import trio_run_with_asyncio

router = APIRouter()

@router.post('/api/jenkins')
@router.get('/api/jenkins')
async def jobs():
    return await getData("JENKINS")
