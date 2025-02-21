import json
import asyncio
import traceback
from multiprocessing import cpu_count
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Query, Response
from fastapi.responses import ORJSONResponse
import pandas as pd

from .maps.ocp import ocpMapper, ocpFilter
from .maps.quay import quayMapper, quayFilter
from .maps.hce import hceMapper, hceFilter
from .maps.telco import telcoMapper, telcoFilter
from .maps.ocm import ocmMapper, ocmFilter
from app.api.v1.commons.example_responses import cpt_200_response, response_422
from app.api.v1.commons.utils import normalize_pagination, get_dict_from_qs
from app.api.v1.commons.constants import FILEDS_DISPLAY_NAMES

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


### **Helper Function for Default Date Handling**
def get_default_dates(start_date, end_date):
    today = datetime.utcnow().date()
    return (start_date or today - timedelta(days=5), end_date or today)


SEMAPHORE = asyncio.Semaphore(5)


async def fetch_data_limited(product, *args, **kwargs):
    async with SEMAPHORE:
        return await fetch_data(product, *args, **kwargs)


### **Unified Fetch Function**
async def fetch_data(
    product, start_date, end_date, size=None, offset=None, filter=None, is_filter=False
):
    try:
        fetch_function = productsFilter[product] if is_filter else products[product]
        args = (
            (start_date, end_date, filter)
            if is_filter
            else (start_date, end_date, size, offset, filter)
        )

        response = await fetch_function(*args)

        if not response:
            return {"data": pd.DataFrame(), "total": 0} if not is_filter else {}

        return {
            "data": (
                response["data"] if not is_filter else response.get("filterData", [])
            ),
            "total": response["total"],
            "summary": response.get("summary", {}),
        }
    except Exception as e:
        print(f"Error fetching data for {product}: {e}\n{traceback.format_exc()}")
        return {"data": pd.DataFrame(), "total": 0} if not is_filter else {}


### **Jobs Endpoint**
@router.get(
    "/api/v1/cpt/jobs",
    summary="Returns a job list from all the products.",
    description="Returns a list of jobs in the specified dates. Defaults: last 5 days.",
    responses={200: cpt_200_response(), 422: response_422()},
)
async def jobs(
    start_date: date = Query(
        None, description="Start date (YYYY-MM-DD)", examples=["2020-11-10"]
    ),
    end_date: date = Query(
        None, description="End date (YYYY-MM-DD)", examples=["2020-11-15"]
    ),
    pretty: bool = Query(False, description="Pretty output format"),
    size: int = Query(None, description="Number of jobs"),
    offset: int = Query(None, description="Offset"),
    filter: str = Query(None, description="Query to filter jobs"),
    totalJobs: int = Query(None, description="Total job count"),
):
    start_date, end_date = get_default_dates(start_date, end_date)

    if start_date > end_date:
        return Response(
            content=json.dumps({"error": "start_date must be before end_date"}),
            status_code=422,
        )

    offset, size = normalize_pagination(offset, size)

    # Run all fetches concurrently
    results = await asyncio.gather(
        *[
            fetch_data_limited(product, start_date, end_date, size, offset, filter)
            for product in products
        ]
    )

    results_df = pd.concat(
        [res["data"] for res in results if not res["data"].empty], ignore_index=True
    )
    total_jobs_count = sum(int(res["total"]) for res in results)

    response = {
        "startDate": str(start_date),
        "endDate": str(end_date),
        "results": results_df.to_dict("records"),
        "total": total_jobs_count if totalJobs == 0 else totalJobs,
        "offset": offset + size,
    }

    return ORJSONResponse(content=response, media_type="application/json")


### **Filters Endpoint**
@router.get(
    "/api/v1/cpt/filters",
    summary="Returns the data to construct filters.",
    description="Returns the filter data for the specified date range. Defaults: last 5 days.",
    responses={200: cpt_200_response(), 422: response_422()},
)
async def filters(
    start_date: date = Query(
        None, description="Start date (YYYY-MM-DD)", examples=["2020-11-10"]
    ),
    end_date: date = Query(
        None, description="End date (YYYY-MM-DD)", examples=["2020-11-15"]
    ),
    pretty: bool = Query(False, description="Pretty output format"),
    filter: str = Query(None, description="Query to filter jobs"),
):
    start_date, end_date = get_default_dates(start_date, end_date)

    if start_date > end_date:
        return Response(
            content=json.dumps({"error": "start_date must be before end_date"}),
            status_code=422,
        )

    filter_dict = get_dict_from_qs(filter) if filter else {}
    prod_list = filter_dict.pop("product", list(productsFilter.keys()))

    # Fetch filters concurrently
    results = await asyncio.gather(
        *[
            fetch_data_limited(
                product, start_date, end_date, filter=filter, is_filter=True
            )
            for product in prod_list
        ]
    )

    total_dict, summary_dict, result_dict = (
        {},
        {"success": 0, "failure": 0, "other": 0, "total": 0},
        {},
    )

    for result in results:
        total_dict[result.get("product", "")] = result.get("total", 0)

        for key, value in result.get("summary", {}).items():
            summary_dict[key] += value

        for item in result.get("data", []):
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

    merged_result = [
        {"key": k, "value": v, "name": FILEDS_DISPLAY_NAMES.get(k, k)}
        for k, v in result_dict.items()
    ]

    response = {
        "startDate": str(start_date),
        "endDate": str(end_date),
        "filterData": merged_result,
        "summary": summary_dict,
        "total": sum(int(v) for v in total_dict.values()),
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type="application/json")

    jsonstring = json.dumps(response)
    return jsonstring
