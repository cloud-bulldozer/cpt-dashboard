from fastapi import APIRouter

from app.api.endpoints import download
from app.api.endpoints import example

api_router = APIRouter()
api_router.include_router(example.router)
api_router.include_router(download.router, 
  # prefix='/api',
 tags=['perfscale'])
