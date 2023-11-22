import json
from fastapi import Response
import pandas as pd
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from .maps.ocp import ocpMapper
from ...commons import responses
from fastapi.param_functions import Query


router = APIRouter()

products = {
            "ocp": ocpMapper,
           }


response_example ={
  "startDate": "2023-11-18",
  "endDate": "2023-11-23",
  "results": [
        {
        "ciSystem": "PROW",
        "uuid": "f6d084d5-b154-4108-b4f7-165094ccc838",
        "releaseStream": "Nightly",
        "jobStatus": "success",
        "buildUrl": "https://ci..org/view/1726571333392797696",
        "startDate": "2023-11-20T13:16:34Z",
        "endDate": "2023-11-20T13:28:48Z",
        "product": "ocp",
        "version": "4.13",
        "testName": "cluster-density-v2"
        },
        {
        "ciSystem": "JENKINS",
        "uuid": "5b729011-3b4d-4ec4-953d-6881ac9da505",
        "releaseStream": "Stable",
        "jobStatus": "success",
        "buildUrl": "https://ci..org/view/1726571333392797696",
        "startDate": "2023-11-20T13:16:30Z",
        "endDate": "2023-11-20T13:30:40Z",
        "product": "ocp",
        "version": "4.14",
        "testName": "node-density-heavy"
        },
    ]
}


@router.get('/api/cpt/v1/jobs',
            summary="Returns a job list from all the products.",
            description="Returns a list of jobs in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
            responses={
                200: responses.response_200(response_example),
                422: responses.response_422(),
            },)
async def jobs(start_date: date = Query(None, description="Start date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-10"]),
                end_date: date = Query(None, description="End date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-15"]),
                pretty: bool = Query(False, description="Output contet in pretty format.")):
    if start_date is None:
        start_date = datetime.utcnow().date()
        start_date = start_date - timedelta(days=5)

    if end_date is None:
        end_date = datetime.utcnow().date()

    if start_date > end_date:
        return Response(content=json.dumps({'error': "invalid date format, start_date must be less than end_date"}), status_code=422)

    results = pd.DataFrame()
    for func in products.values():
        df = await func(start_date, end_date)
        results = pd.concat([results, df])

    response = {
        'startDate': start_date.__str__(),
        'endDate': end_date.__str__(),
        'results': results.to_dict('records')
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')

    jsonstring = json.dumps(response)
    return jsonstring
