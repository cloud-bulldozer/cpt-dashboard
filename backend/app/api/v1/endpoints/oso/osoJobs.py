from datetime import date, datetime, timedelta
import json

from fastapi import APIRouter, Response
from fastapi.param_functions import Query

from app.api.v1.commons.utils import normalize_pagination

from ...commons.example_responses import (
    oso_200_response,
    oso_filter_200_response,
    response_422,
)
from ...commons.oso import getData, getFilterData

router = APIRouter()


@router.get(
    "/api/v1/oso/jobs",
    summary="Returns a job list",
    description="Returns a list of jobs in the specified dates. \
            If dates are not provided the API will use the following values as defaults: \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: oso_200_response(),
        422: response_422(),
    },
)
async def jobs(
    start_date: date = Query(
        None,
        description="Start date for searching jobs, format: 'YYYY-MM-DD'",
        examples=["2020-11-10"],
    ),
    end_date: date = Query(
        None,
        description="End date for searching jobs, format: 'YYYY-MM-DD'",
        examples=["2020-11-15"],
    ),
    pretty: bool = Query(False, description="Output content in pretty format."),
    size: int = Query(None, description="Number of jobs to fetch"),
    offset: int = Query(None, description="Offset Number to fetch jobs from"),
    sort: str = Query(None, description="To sort fields on specified direction"),
    filter: str = Query(None, description="Query to filter the jobs"),
):
    if start_date is None:
        start_date = datetime.utcnow().date()
        start_date = start_date - timedelta(days=5)

    if end_date is None:
        end_date = datetime.utcnow().date()

    if start_date > end_date:
        return Response(
            content=json.dumps(
                {"error": "invalid date format, start_date must be less than end_date"}
            ),
            status_code=422,
        )

    offset, size = normalize_pagination(offset, size)
    results = await getData(
        start_date, end_date, size, offset, sort, filter, "oso.elasticsearch"
    )
    jobs = []
    if "data" in results and len(results["data"]) >= 1:
        jobs = results["data"].to_dict("records")

    response = {
        "startDate": start_date.__str__(),
        "endDate": end_date.__str__(),
        "results": jobs,
        "total": results["total"],
        "offset": offset + size,
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type="application/json")

    jsonstring = json.dumps(response)
    return jsonstring


@router.get(
    "/api/v1/oso/filters",
    summary="Returns the data to construct filters",
    description="Returns the data to build filters in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: oso_filter_200_response(),
        422: response_422(),
    },
)
async def filters(
    start_date: date = Query(
        None,
        description="Start date for searching jobs, format: 'YYYY-MM-DD'",
        examples=["2020-11-10"],
    ),
    end_date: date = Query(
        None,
        description="End date for searching jobs, format: 'YYYY-MM-DD'",
        examples=["2020-11-15"],
    ),
    pretty: bool = Query(False, description="Output content in pretty format."),
    filter: str = Query(None, description="Query to filter the jobs"),
):
    if start_date is None:
        start_date = datetime.utcnow().date()
        start_date = start_date - timedelta(days=5)

    if end_date is None:
        end_date = datetime.utcnow().date()

    if start_date > end_date:
        return Response(
            content=json.dumps(
                {"error": "invalid date format, start_date must be less than end_date"}
            ),
            status_code=422,
        )

    results = await getFilterData(start_date, end_date, filter, "oso.elasticsearch")

    if len(results["filterData"]) > 0:
        json_str = json.dumps(results, indent=4)
        return Response(content=json_str, media_type="application/json")
    else:
        json_str = json.dumps(results, indent=4)
        return Response(content=json_str, media_type="application/json")
