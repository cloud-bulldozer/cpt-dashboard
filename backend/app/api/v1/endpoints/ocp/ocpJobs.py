import json
from typing import Optional
from fastapi import Body, Response
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from ...commons.ocp import getData, getFilterData
from ...commons.example_responses import ocp_200_response, response_422
from fastapi.param_functions import Query

router = APIRouter()



@router.get('/api/v1/ocp/jobs',
            summary="Returns a job list",
            description="Returns a list of jobs in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
            responses={
                200: ocp_200_response(),
                422: response_422(),
        },)
async def jobs(start_date: date = Query(None, description="Start date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-10"]),
                end_date: date = Query(None, description="End date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-15"]),
                pretty: bool = Query(False, description="Output contet in pretty format."),
                size: int = Query(None, description="Number of jobs to fetch"),
                offset: int = Query(None, description="Offset Number to fetch jobs from"),
                sort: str = Query(None, description="To sort the field on specified direction"),
                filter: str = Query(None, description="Filter jobs")
                ):
    try:
        if start_date is None:
            start_date = datetime.utcnow().date()
            start_date = start_date - timedelta(days=5)

        if end_date is None:
            end_date = datetime.utcnow().date()

        if start_date > end_date:
            return Response(content=json.dumps({'error': "invalid date format, start_date must be less than end_date"}), status_code=422)
        
        results = await getData(start_date, end_date, size, offset, sort, filter, 'ocp.elasticsearch')

        if len(results["data"]) >= 1:
            response = {
                'startDate': start_date.__str__(),
                'endDate': end_date.__str__(),
                'results': results["data"].to_dict('records'),
                'total': results["total"], 
                'offset': offset + size
            }
        else :
            response = {
                'startDate': start_date.__str__(),
                'endDate': end_date.__str__(),
                'results': [],
                'total': 0,
                'offset': 0
            }

        if pretty:
            json_str = json.dumps(response, indent=4)
            return Response(content=json_str, media_type='application/json')

        jsonstring = json.dumps(response)
        return jsonstring
    
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}") 

@router.get('/api/v1/ocp/filters',
            summary="Returns a job list",
            description="Returns a list of jobs in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
            responses={
                200: ocp_200_response(),
                422: response_422(),
        },)
async def filters(start_date: date = Query(None, description="Start date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-10"]),
                end_date: date = Query(None, description="End date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-15"]),
                pretty: bool = Query(False, description="Output contet in pretty format."),
                size: int = Query(None, description="Number of jobs to fetch"),
                offset: int = Query(None, description="Offset Number to fetch jobs from"),
                sort: str = Query(None, description="To sort the field on specified direction"),
                filter: str = Query(None, description="Filter jobs")):
    try:
        if start_date is None:
            start_date = datetime.utcnow().date()
            start_date = start_date - timedelta(days=5)

        if end_date is None:
            end_date = datetime.utcnow().date()

        if start_date > end_date:
            return Response(content=json.dumps({'error': "invalid date format, start_date must be less than end_date"}), status_code=422)
        
        results = await getFilterData(start_date, end_date, size, offset, sort, filter, 'ocp.elasticsearch')
        
        if len(results) > 0:
            print(results)
        else:
            print("No data")
        
        json_str = json.dumps(results, indent=4)
        return Response(content=json_str, media_type='application/json')
        
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}") 
        