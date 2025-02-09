import json
import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from fastapi import Response
import pandas as pd
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from .maps.ocp import ocpMapper, ocpFilter
from .maps.quay import quayMapper, quayFilter
from .maps.hce import hceMapper, hceFilter
from .maps.telco import telcoMapper, telcoFilter
from .maps.ocm import ocmMapper, ocmFilter
from app.api.v1.commons.example_responses import cpt_200_response, response_422
from fastapi.param_functions import Query
from app.api.v1.commons.utils import normalize_pagination, get_dict_from_qs
from app.api.v1.commons.constants import FILEDS_DISPLAY_NAMES
from urllib.parse import urlencode
import traceback

router = APIRouter()

products = {
    "ocp": ocpMapper,
    "quay": quayMapper,
    "hce": hceMapper,
    "telco": telcoMapper,
    "ocm": ocmMapper,
}

productsFilter = {
    "ocp": ocpFilter,
    "quay": quayFilter,
    "hce": hceFilter,
    "telco": telcoFilter,
    "ocm": ocmFilter,
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
    filter: str = Query(None, description="Query to filter the jobs"),
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

    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = {
            executor.submit(
                fetch_product, product, start_date, end_date, size, offset, filter
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

    # The total is determined by summing the counts of all products and is included in the response.
    # However, during pagination, if the count of any product drops to zero,
    # the total becomes lower than the actual value, which is undesirable.

    # on first hit, totalJobs is 0
    jobsCount = (
        sum(int(v) for v in total_dict.values()) if totalJobs == 0 else totalJobs
    )

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


async def fetch_product_async(product, start_date, end_date, size, offset, filter):
    try:
        response = await products[product](start_date, end_date, size, offset, filter)
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


def fetch_product(product, start_date, end_date, size, offset, filter):
    return asyncio.run(
        fetch_product_async(product, start_date, end_date, size, offset, filter)
    )


async def fetch_product_filter_async(product, start_date, end_date, filter):
    try:
        response = await productsFilter[product](start_date, end_date, filter)
        if response:
            return {
                "filterData": response.get("filterData", []),
                "total": response.get("total", 0),
                "summary": response.get("summary", {}),
            }
    except ConnectionError:
        print("Connection Error in filter for product " + product)
    except Exception as e:
        print(f"Error in filter for product {product}: {e}")
        print(traceback.format_exc())
        return {}


def fetch_product_filter(product, start_date, end_date, filter):
    return asyncio.run(
        fetch_product_filter_async(product, start_date, end_date, filter)
    )


@router.get(
    "/api/v1/cpt/filters",
    summary="Returns the data to construct filters",
    description="Returns the data to build filters in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
    responses={
        200: cpt_200_response(),
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
    total_dict = {}
    result_dict = {}
    summary_dict = {"success": 0, "failure": 0, "other": 0, "total": 0}
    filter_dict = get_dict_from_qs(filter) if filter else {}
    merged_result = []
    made_up_prod = {"ocp", "ocm", "telco", "quay"}
    if filter:
        refiner = (
            filter_dict.pop("product", None)
            if "product" in filter_dict
            and any(p in made_up_prod for p in filter_dict["product"])
            else ["hce"]
        )

        prod_list = refiner if "product" in filter_dict else productsFilter
    else:
        prod_list = productsFilter

    with ThreadPoolExecutor(max_workers=cpu_count() * 2) as executor:
        futures = {
            executor.submit(
                fetch_product_filter, product, start_date, end_date, filter
            ): product
            for product in prod_list
        }
        for future in as_completed(futures):
            product = futures[future]
            try:
                result = future.result()
                total_dict[product] = result.get("total", 0)

                summary = result.get("summary", {})
                for key in summary_dict:
                    summary_dict[key] += summary.get(key, 0)

                for item in result.get("filterData", []):
                    key, values = item["key"], item["value"]

                    # If the key already exists, merge the values
                    if key in result_dict:
                        if isinstance(values[0], str):
                            existing_values = {v.lower(): v for v in result_dict[key]}
                            for val in values:
                                if val.lower() not in existing_values and val != "":
                                    result_dict[key].append(val)
                        else:
                            # For numbers (version), just avoid duplicates
                            result_dict[key] = list(set(result_dict[key] + values))
                    else:
                        result_dict[key] = [s for s in values if str(s).strip()]
            except Exception as e:
                print(f"Error fetching filter for product {product}: {e}")

    merged_result = [
        {"key": k, "value": v, "name": FILEDS_DISPLAY_NAMES[k]}
        for k, v in result_dict.items()
    ]
    response = {
        "startDate": start_date.__str__(),
        "endDate": end_date.__str__(),
        "filterData": merged_result,
        "summary": summary_dict,
        "total": sum(int(v) for v in total_dict.values()),
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type="application/json")

    jsonstring = json.dumps(response)
    return jsonstring
