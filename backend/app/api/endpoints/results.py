from fastapi import APIRouter

from app.core import elastic_transform
from app.services.elasticsearch import ElasticService

from pprint import pprint


router = APIRouter()


@router.post('/api/results')
@router.get('/api/results')
async def results(
    query={
        'query': {
            'range': {
                'timestamp': {
                    'format': 'strict_date_optional_time',
                    'gte': 'now-3M',
                    'lte': 'now'
                }
            }
        }
    }
):
    es = ElasticService()
    response = {}
    response = await es.post(query)
    await es.close()

    return elastic_transform.build_results_dataframe(response)


@router.get('/api/results/{pipeline_id}/{job_id}')
async def results_for_job(pipeline_id: str, job_id: str):
    print(job_id)
    query = {
        "query": {
            "query_string": {
                "query": f"upstream_job: \"{pipeline_id}\" AND upstream_job_build: \"{job_id}\"",
            }
        }
    }

    es = ElasticService()
    response = {}
    response = await es.post(query)
    await es.close()
    return [item['_source'] for item in response["hits"]["hits"]]
