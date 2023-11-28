from fastapi import APIRouter
from fastapi.param_functions import Path

from app.services.search import ElasticService

router = APIRouter()


@router.get('/api/ocp/v1/jobs/{ci}/{job_id}',
            summary="Returns the details of a specified Job.")
async def results_for_job(
        ci: str = Path(..., description="Name of the CI system tha tthe job belongs to.", examples=["PROW", "JENKINS"]),
        job_id: str = Path(..., description="Unique identifier of the Jon, normally the UUID.", examples=["8b671d0b-8638-4423-b453-cc54b1caf529"])):
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'uuid: "{job_id}"')
            }
        }
    }

    es = ElasticService(configpath="ocp.elasticsearch")
    response = await es.post(query)
    await es.close()
    tasks = [item['_source'] for item in response["hits"]["hits"]]
    return tasks
