import json
from fastapi import Response
import pandas as pd
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from .maps.ocp import ocpMapper
from .maps.quay import quayMapper
from .maps.hce import hceMapper
from .maps.rhoai import rhoaiNotebooksPerformanceMapper
from ...commons.example_responses import cpt_200_response, response_422
from fastapi.param_functions import Query

router = APIRouter()

products = {
            "ocp": ocpMapper,
            "quay": quayMapper,
            "hce": hceMapper,
            "rhoai": rhoaiNotebooksPerformanceMapper,
           }

@router.get('/api/v1/cpt/jobs',
            summary="Returns a job list from all the products.",
            description="Returns a list of jobs in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
            responses={
                200: cpt_200_response(),
                422: response_422(),
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
    for product in products:
        try:
            df = await products[product](start_date, end_date, f'{product}.elasticsearch')
            results = pd.concat([results, df.loc[:, ["ciSystem", "uuid", "releaseStream", "jobStatus", "buildUrl", "startDate", "endDate", "product", "version", "testName"]]])
        except ConnectionError:
            print("Connection Error in mapper for product " + product)
        except Exception as e: # DANGEROUS
            print("Date range returned no values or Unknown error in mapper for product " + product + " | " + str(e))
            raise e

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
