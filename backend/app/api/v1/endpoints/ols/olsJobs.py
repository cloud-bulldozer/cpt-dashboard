from datetime import date
from fastapi import APIRouter
from ...endpoints.ocp.ocpJobs import jobs as ocpJobs
from ...endpoints.ocp.ocpJobs import filters as ocpFilters
from ...commons.example_responses import (
    ols_200_response,
    response_422,
    ocp_filter_200_response,
)
from fastapi.param_functions import Query


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

    return await ocpJobs(start_date, end_date, 
                         pretty, size, offset, sort, 
                         filter="benchmark='ols-load-generator'")


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

    return await ocpFilters(start_date, end_date, pretty, filter)
