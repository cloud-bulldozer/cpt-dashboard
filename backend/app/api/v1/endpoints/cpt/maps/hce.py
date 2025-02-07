from app.api.v1.commons.hce import getData, getFilterData
from datetime import date
import pandas as pd
from app.api.v1.commons.constants import keys_to_keep
from urllib.parse import urlencode, parse_qs


################################################################
# This will return a Dictionary from HCE required by the CPT
#  endpoint, it contians totalJobs and a Dataframe with the following columns:
#   "ciSystem"
#   "uuid"
#   "releaseStream"
#   "jobStatus"
#   "buildUrl"
#   "startDate"
#   "endDate"
#   "product"
#   "version"
#   "testName"
################################################################
async def hceMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    response = await getData(
        start_datetime, end_datetime, size, offset, filter, f"hce.elasticsearch"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"data": pd.DataFrame(), "total": 0}
    df = response.get("data", pd.DataFrame())
    if df.empty:
        return {"data": df, "total": response.get("total", 0)}

    df["releaseStream"] = "Nightly"
    df["ciSystem"] = "Jenkins"
    df["testName"] = df["product"] + ":" + df["test"]
    df["product"] = df["group"]
    df["jobStatus"] = df["result"].apply(
        lambda x: "SUCCESS" if x == "PASS" else "FAILURE"
    )
    df["version"] = df["version"].apply(
        lambda x: x if len(x.split(":")) == 1 else x.split(":")[1][:7]
    )
    df["uuid"] = df["result_id"]
    df["buildUrl"] = df["link"]
    df["startDate"] = df["date"]
    df["endDate"] = df["date"]
    df = dropColumns(df)
    return {"data": df, "total": response.get("total", 0)}


def dropColumns(df):
    df = df.drop(
        columns=["group", "test", "result", "result_id", "link", "date", "release"]
    )
    return df


async def hceFilter(start_datetime: date, end_datetime: date, filter: str):
    updated_filter = filter
    if filter:
        query_params = parse_qs(filter)
        # Change a field if it exists
        if "jobStatus" in query_params:
            query_params["result"] = query_params.pop("jobStatus")
            updated_filter = urlencode(query_params, doseq=True)
    print(updated_filter)
    response = await getFilterData(
        start_datetime, end_datetime, updated_filter, f"hce.elasticsearch"
    )

    if isinstance(response, pd.DataFrame) or not response:
        return {"total": 0, "filterData": [], "summary": {}}

    if not response.get("filterData") or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}

    # Add predefined filters
    filters_to_add = [
        {"key": "ciSystem", "name": "CI System", "value": ["Jenkins"]},
        {"key": "releaseStream", "name": "Release Stream", "value": ["Nightly"]},
    ]
    response["filterData"].extend(filters_to_add)

    # Filter data based on allowed keys
    filtered_data = [
        item for item in response["filterData"] if item.get("key") in keys_to_keep
    ]
    print("hce summary")
    print(response["summary"])
    return {
        "total": response.get("total", 0),
        "filterData": filtered_data,
        "summary": response.get("summary", {}),
    }
