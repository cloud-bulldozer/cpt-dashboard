from app.api.v1.commons.quay import getData, getFilterData
from datetime import date
import pandas as pd
from app.api.v1.commons.constants import keys_to_keep
from urllib.parse import urlencode
from app.api.v1.commons.utils import get_dict_from_qs


#####################################################################################
# This will return a DataFrame from Quay required by the CPT endpoint with Total jobs
#####################################################################################
async def quayMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    sort = None

    updated_filter = await get_updated_filter(filter)

    response = await getData(
        start_datetime,
        end_datetime,
        size,
        offset,
        sort,
        updated_filter,
        f"quay.elasticsearch",
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"data": pd.DataFrame(), "total": 0}

    df = response.get("data", pd.DataFrame())
    if df.empty:
        return {"data": df, "total": response.get("total", 0)}

    df.insert(len(df.columns), "product", "quay")
    df["version"] = df["releaseStream"]
    df["testName"] = df["benchmark"]
    return {"data": df, "total": response.get("total", 0)}


async def quayFilter(start_datetime: date, end_datetime: date, filter: str):
    updated_filter = await get_updated_filter(filter)

    response = await getFilterData(
        start_datetime, end_datetime, updated_filter, f"quay.elasticsearch"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"total": 0, "filterData": [], "summary": {}}

    if not response.get("filterData") or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}

    # Normalize filters
    for item in response["filterData"]:
        if item.get("key") == "benchmark":
            item.update({"key": "testName", "name": "Test Name"})

    # Add predefined filters
    filters_to_add = [
        {"key": "product", "name": "Product", "value": ["quay"]},
    ]
    response["filterData"].extend(filters_to_add)

    # Filter data based on allowed keys
    filtered_data = [
        item for item in response["filterData"] if item.get("key") in keys_to_keep
    ]
    return {
        "total": response.get("total", 0),
        "filterData": filtered_data,
        "summary": response.get("summary", {}),
    }


async def get_updated_filter(filter):
    if not filter:
        return ""

    query_params = get_dict_from_qs(filter)

    # Map Test Name to Benchmark
    if "testName" in query_params:
        query_params["benchmark"] = query_params.pop("testName")
    # Remove product from the query params as all products will be quay
    query_params.pop("product", None)
    return urlencode(query_params, doseq=True) if query_params else ""
