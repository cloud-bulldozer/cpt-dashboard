import json
from fastapi import Response
from datetime import datetime
from fastapi import APIRouter
from ...commons.example_responses import stub_results, stub_columns, stub_filters
from fastapi.param_functions import Query
import pandas as pd


router = APIRouter()


@router.get('/api/v1/stub/jobs',
            summary="Returns a stub job list",
            description="Returns a list of jobs. Includes a list of Columns, and Filters.",
            responses={
                # 200: ocp_200_response(),
                # 422: response_422(),
            },)
async def jobs(pretty: bool = Query(False, description="Output contet in pretty format.")):
    results = stub_results()["results"]
    dfItem = pd.json_normalize(results)
    print(dfItem)

    response = {
        'startDate': datetime.utcnow().date().__str__(),
        'endDate': datetime.utcnow().date().__str__(),
        'results': dfItem.to_dict('records'),
        'columns': stub_columns(),
        'filters': stub_filters()
    }

    return Response(content=json.dumps(response), media_type='application/json')
