from datetime import date
from urllib.parse import urlencode

import pandas as pd

from app.api.v1.commons.constants import keys_to_keep
from app.api.v1.commons.telco import getData, getFilterData
from app.api.v1.commons.utils import get_dict_from_qs


#####################################################################
# This will return a DataFrame from Telco required by the CPT endpoint
#####################################################################
async def telcoMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    updated_filter = await get_updated_telco_filter(filter)
    sort = None
    response = await getData(
        start_datetime,
        end_datetime,
        size,
        offset,
        sort,
        updated_filter,
        "telco.splunk",
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {
            "data": pd.DataFrame(),
            "total": 0,
        }

    df = response.get("data", pd.DataFrame())

    if df.empty:
        return {"data": df, "total": response.get("total", 0)}

    df["product"] = "telco"
    df["version"] = df.get("shortVersion", "")
    df["testName"] = df.get("benchmark", "")

    return {"data": df, "total": response.get("total", 0)}


async def telcoFilter(start_datetime: date, end_datetime: date, filter: str):
    try:
        query_params = get_dict_from_qs(filter)
        # CI System must be Jenkins for all jobs in Telco
        if "ciSystem" in query_params and not any(
            item.lower() == "jenkins" for item in query_params.get("ciSystem", [])
        ):
            return {"total": 0, "filterData": [], "summary": {}}

        updated_filter = await get_updated_telco_filter(filter)

        response = await getFilterData(
            start_datetime, end_datetime, updated_filter, "telco.splunk"
        )

        if isinstance(response, pd.DataFrame) or not response:
            return {"total": 0, "filterData": [], "summary": {}}

        if not response.get("data") or response.get("total", 0) == 0:
            return {"total": response.get("total", 0), "filterData": [], "summary": {}}

        for item in response["data"]:
            if item.get("key") == "benchmark":
                item.update({"key": "testName", "name": "Test Name"})

        # Add predefined filters
        filters_to_add = [
            {"key": "product", "name": "Product", "value": ["telco"]},
            {"key": "ciSystem", "name": "CI System", "value": ["Jenkins"]},
        ]
        response["data"].extend(filters_to_add)

        # Filter data based on allowed keys
        filtered_data = [
            item for item in response["data"] if item.get("key") in keys_to_keep
        ]

        return {
            "total": response.get("total", 0),
            "filterData": filtered_data,
            "summary": response.get("summary", {}),
        }
    except Exception as e:
        print(f"Error fetching filter for product telco: {e}")


async def get_updated_telco_filter(filter):
    if not filter:
        return ""

    query_params = get_dict_from_qs(filter)

    # Rename testName to benchmark
    if "testName" in query_params:
        query_params["benchmark"] = query_params.pop("testName")
    # Remove ciSystem from the query params
    query_params.pop("ciSystem", None)
    # Remove product from the query params as all products will be telco
    query_params.pop("product", None)
    return urlencode(query_params, doseq=True) if query_params else ""
