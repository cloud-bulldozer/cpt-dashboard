from app.api.v1.commons.telco import getData, getFilterData
from app.api.v1.commons.utils import getReleaseStream
from app.api.v1.commons.constants import keys_to_keep
from datetime import date
import pandas as pd


#####################################################################
# This will return a DataFrame from Telco required by the CPT endpoint
#####################################################################
async def telcoMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    response = await getData(
        start_datetime, end_datetime, size, offset, filter, f"telco.splunk"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {
            "data": pd.DataFrame(),
            "total": 0,
        }

    df = response.get("data", pd.DataFrame())

    if df.empty:
        return df

    df["product"] = "telco"
    df["releaseStream"] = df.apply(getReleaseStream, axis=1)
    df["version"] = df.get("shortVersion", "")
    df["testName"] = df.get("benchmark", "")

    return {"data": df, "total": response.get("total", 0)}


async def telcoFilter(start_datetime: date, end_datetime: date, filter: str):

    response = await getFilterData(start_datetime, end_datetime, filter, "telco.splunk")

    if isinstance(response, pd.DataFrame) or not response:
        return {"total": 0, "filterData": []}

    if not response.get("data") or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": []}

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
    }
