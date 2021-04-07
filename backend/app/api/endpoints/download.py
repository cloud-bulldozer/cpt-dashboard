from fastapi import APIRouter

from app.core import transform
from app.models.query import Query
from app.services.elasticsearch_api import Elasticsearch_API

from pprint import pprint


router = APIRouter()


@router.post('/api/download')
async def download(
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
    # query: Query = Query(
    # query = {
    #     'range': {
    #         'timestamp': {
    #             'format': 'strict_date_optional_time',
    #             'gte': 'now-3M',
    #             'lte': 'now'
    #         }
    #     }
    # })    
):
    es = Elasticsearch_API()
    response = {}

    # pprint(query)

    # try:
    # first get the es response
    response = await es.post(query)
    # pprint(response)
    await es.close()

    

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

    # pprint(response['hits']['hits'])
    # pprint(transform.extract_to_long_df(response['hits']['hits']))
    
    return transform.build_results_dataframe(response)

