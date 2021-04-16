from fastapi import APIRouter

from app.api.endpoints import results
from app.api.endpoints import example
from app.api.endpoints import airflow

api_router = APIRouter()
api_router.include_router(example.router)
api_router.include_router(results.router, tags=['perfscale'])
api_router.include_router(airflow.router, tags=['perfscale'])
