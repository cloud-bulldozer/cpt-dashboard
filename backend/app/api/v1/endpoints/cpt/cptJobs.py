import json
import asyncio
import multiprocessing
from fastapi import Response
import pandas as pd
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from .maps.ocp import ocpMapper
from .maps.quay import quayMapper
from .maps.hce import hceMapper
from .maps.telco import telcoMapper
from ...commons.example_responses import cpt_200_response, response_422
from fastapi.param_functions import Query

router = APIRouter()

products = {
            "ocp": ocpMapper,
            "quay": quayMapper,
            "hce": hceMapper,
            "telco": telcoMapper,
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

    results_df = pd.DataFrame()
    with multiprocessing.Pool() as pool:
        results = [pool.apply(fetch_product, args=(product, start_date, end_date)) for product in products]
        results_df = pd.concat(results)

    response = {
        'startDate': start_date.__str__(),
        'endDate': end_date.__str__(),
        'results': results_df.to_dict('records')
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')

    jsonstring = json.dumps(response)
    return jsonstring

async def fetch_product_async(product, start_date, end_date):
    try:
        df = await products[product](start_date, end_date)
        return df.loc[:, ["ciSystem", "uuid", "releaseStream", "jobStatus", "buildUrl", "startDate", "endDate", "product", "version", "testName"]] if len(df) != 0 else df
    except ConnectionError:
        print("Connection Error in mapper for product " + product)
    except Exception as e:
        print(f"Error in mapper for product {product}: {e}")
        return pd.DataFrame()

def fetch_product(product, start_date, end_date):
    return asyncio.run(fetch_product_async(product, start_date, end_date))