from app.api.v1.commons.ocp import getData, getFilterData
from app.api.v1.commons.utils import getReleaseStream, buildReleaseStreamFilter
from datetime import date
import pandas as pd
from app.api.v1.commons.constants import keys_to_keep


################################################################
# This will return a DataFrame from OCP required by the CPT endpoint
################################################################
async def ocpMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    response = await getData(
        start_datetime, end_datetime, size, offset, filter, f"ocp.elasticsearch"
    )

    if not isinstance(response, pd.DataFrame) and response:
        df = response["data"]
        if len(df) == 0:
            return df
        df.insert(len(df.columns), "product", "ocp")
        df["releaseStream"] = df.apply(getReleaseStream, axis=1)
        df["version"] = df["shortVersion"]
        df["testName"] = df["benchmark"]
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": response["total"]}


async def ocpFilter(start_datetime: date, end_datetime: date, filter: str):
    response = await getFilterData(
        start_datetime, end_datetime, filter, f"ocp.elasticsearch"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"total": 0, "filterData": [], "summary": {}}

    if not response.get("filterData") or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}

    # Normalize filters
    for item in response["filterData"]:
        if item.get("key") == "releaseStream":
            current_values = item.get("value", [])
            updated_values = buildReleaseStreamFilter(current_values)
            item["value"] = updated_values
        if item.get("key") == "benchmark":
            item.update({"key": "testName", "name": "Test Name"})

    # Add predefined filters
    filters_to_add = [
        {"key": "product", "name": "Product", "value": ["ocp"]},
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
