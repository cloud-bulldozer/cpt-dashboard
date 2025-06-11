from datetime import date, datetime, timedelta
import json

from fastapi import APIRouter, Response
from fastapi.param_functions import Query

from ...commons.example_responses import (
    ocp_filter_200_response,
    ols_200_response,
    response_422,
)
from ...commons.ols import getFilterData
from ...endpoints.ocp.ocpJobs import jobs as ocpJobs

router = APIRouter()


@router.get(
    "/api/v1/ols/jobs",
    summary="Returns a job list",
    description="Returns a list of jobs in the specified dates. \
            If dates are not provided the API will use the following values as defaults: \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: ols_200_response(),
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
    filter_clause = "benchmark='ols-load-generator'"
    filter = (
        filter_clause
        if not filter
        else filter if filter_clause in filter else f"{filter}&{filter_clause}"
    )
    return await ocpJobs(start_date, end_date, pretty, size, offset, sort, filter)


@router.get(
    "/api/v1/ols/filters",
    summary="Returns the data to construct filters",
    description="Returns the data to build filters in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: ocp_filter_200_response(),
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
    filter_clause = "benchmark='ols-load-generator'"
    filter = (
        filter_clause
        if not filter
        else filter if filter_clause in filter else f"{filter}&{filter_clause}"
    )
    results = await getFilterData(start_date, end_date, filter, "ocp.elasticsearch")

    if len(results["filterData"]) > 0:
        json_str = json.dumps(results, indent=4)
        return Response(content=json_str, media_type="application/json")
    else:
        response = {"filterData": [], "summary": {}}
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type="application/json")
