from fastapi import APIRouter

from app.core import transform
from app.services.elasticsearch_api import Elasticsearch_API

from pprint import pprint


router = APIRouter()


@router.post('/api/results')
async def results(
    query = { 
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
    es = Elasticsearch_API()
    response = {}
    response = await es.post(query)
    await es.close()
    
    return transform.build_results_dataframe(response)



