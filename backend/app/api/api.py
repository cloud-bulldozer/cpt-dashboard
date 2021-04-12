from fastapi import APIRouter

from app.api.endpoints import results
from app.api.endpoints import example

api_router = APIRouter()
api_router.include_router(example.router)
api_router.include_router(results.router, 
  # prefix='/api',
 tags=['perfscale'])
