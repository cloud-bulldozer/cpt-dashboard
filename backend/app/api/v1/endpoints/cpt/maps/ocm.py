from app.api.v1.commons.ocm import getData, getFilterData
from datetime import date
import pandas as pd
from app.api.v1.commons.constants import keys_to_keep


################################################################
# This will return a DataFrame from OCM required by the CPT endpoint
################################################################
async def ocmMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    response = await getData(
        start_datetime, end_datetime, size, offset, filter, f"ocm.elasticsearch"
    )
    if isinstance(response, pd.DataFrame) or not response:
        df = response["data"]
        if len(df) == 0:
            return {"data": df, "total": 0}
        df.insert(len(df.columns), "product", "ocm")
        df.insert(len(df.columns), "releaseStream", "Nightly")
        df["testName"] = df["attack"]
        df["startDate"] = df["metrics.earliest"]
        df["endDate"] = df["metrics.end"]
        return {
            "data": df,
            "total": response["total"],
        }
    return {"data": pd.DataFrame(), "total": 0}


async def ocmFilter(start_datetime: date, end_datetime: date, filter: str):
    response = await getFilterData(
        start_datetime, end_datetime, filter, f"ocm.elasticsearch"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"total": 0, "filterData": [], "summary": {}}

    if not response.get("filterData") or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}

    # Add predefined filters
    filters_to_add = [
        {"key": "product", "name": "Product", "value": ["ocm"]},
        {"key": "releaseStream", "name": "Release Stream", "value": ["Nightly"]},
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
