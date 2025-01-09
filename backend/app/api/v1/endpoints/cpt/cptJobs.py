import json
import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from fastapi import Response, HTTPException
import pandas as pd
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from .maps.ocp import ocpMapper
from .maps.quay import quayMapper
from .maps.hce import hceMapper
from .maps.telco import telcoMapper
from .maps.ocm import ocmMapper
from app.api.v1.commons.example_responses import cpt_200_response, response_422
from fastapi.param_functions import Query
from app.api.v1.commons.utils import normalize_pagination

router = APIRouter()

products = {
    "ocp": ocpMapper,
    "quay": quayMapper,
    "hce": hceMapper,
    "telco": telcoMapper,
    "ocm": ocmMapper,
}


@router.get(
    "/api/v1/cpt/jobs",
    summary="Returns a job list from all the products.",
    description="Returns a list of jobs in the specified dates of requested size \
            If dates are not provided the API will default the values: \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: cpt_200_response(),
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
    totalJobs: int = Query(None, description="Total number of jobs"),
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

    results_df = pd.DataFrame()
    total_dict = {}
    total = 0
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = {
            executor.submit(
                fetch_product, product, start_date, end_date, size, offset
            ): product
            for product in products
        }
        for future in as_completed(futures):
            product = futures[future]
            try:
                result = future.result()
                total_dict[product] = result["total"]
                results_df = pd.concat([results_df, result["data"]])
            except Exception as e:
                print(f"Error fetching data for product {product}: {e}")

    jobsCount = totalJobs
    # The total is determined by summing the counts of all products and is included in the response.
    # However, during pagination, if the count of any product drops to zero,
    # the total becomes lower than the actual value, which is undesirable.

    # on first hit, totalJobs is 0
    if totalJobs == 0:
        for product in total_dict:
            total += int(total_dict[product])
        jobsCount = total
    response = {
        "startDate": start_date.__str__(),
        "endDate": end_date.__str__(),
        "results": results_df.to_dict("records"),
        "total": jobsCount,
        "offset": offset + size,
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type="application/json")

    jsonstring = json.dumps(response)
    return jsonstring


async def fetch_product_async(product, start_date, end_date, size, offset):
    try:
        response = await products[product](start_date, end_date, size, offset)
        if response:
            df = response["data"]
            return {
                "data": (
                    df.loc[
                        :,
                        [
                            "ciSystem",
                            "uuid",
                            "releaseStream",
                            "jobStatus",
                            "buildUrl",
                            "startDate",
                            "endDate",
                            "product",
                            "version",
                            "testName",
                        ],
                    ]
                    if len(df) != 0
                    else df
                ),
                "total": response["total"],
            }
    except ConnectionError:
        print("Connection Error in mapper for product " + product)
    except Exception as e:
        print(f"Error in mapper for product {product}: {e}")
        return pd.DataFrame()


def fetch_product(product, start_date, end_date, size, offset):
    return asyncio.run(fetch_product_async(product, start_date, end_date, size, offset))


def is_requested_size_available(total_count, offset, requested_size):
    """
    Check if the requested size of data is available starting from a given offset.

    Args:
        total_count (int): Total number of available records.
        offset (int): The starting position in the dataset.
        requested_size (int): The number of records requested.

    Returns:
        bool: True if the requested size is available, False otherwise.
    """
    return (offset + requested_size) <= total_count


def calculate_remaining_data(total_count, offset, requested_size):
    """
    Calculate the remaining number of data items that can be fetched based on the requested size.

    Args:
        total_count (int): Total number of available records.
        offset (int): The starting position in the dataset.
        requested_size (int): The number of records requested.

    Returns:
        int: The number of records that can be fetched, which may be less than or equal to requested_size.
    """
    available_data = total_count - offset  # Data available from the offset
    return min(available_data, requested_size)
