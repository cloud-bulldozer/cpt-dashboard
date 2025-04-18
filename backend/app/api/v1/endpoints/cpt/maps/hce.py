from app.api.v1.commons.hce import getData, getFilterData
from datetime import date
import pandas as pd
from app.api.v1.commons.constants import keys_to_keep
from urllib.parse import urlencode
from app.api.v1.commons.utils import get_dict_from_qs
import traceback


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
    query_params = get_dict_from_qs(filter)

    isCriteriaMet = await mandatory_filter_checks(query_params)
    if not isCriteriaMet:
        return {"data": pd.DataFrame(), "total": 0}

    updated_filter = await get_updated_filter(filter)

    response = await getData(
        start_datetime, end_datetime, size, offset, updated_filter, f"hce.elasticsearch"
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
    try:
        query_params = get_dict_from_qs(filter)

        isCriteriaMet = await mandatory_filter_checks(query_params)
        if not isCriteriaMet:
            return {"total": 0, "filterData": [], "summary": {}}
        updated_filter = await get_updated_filter(filter)

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

        return {
            "total": response.get("total", 0),
            "filterData": filtered_data,
            "summary": response.get("summary", {}),
        }
    except Exception as e:
        print(f"Error retrieving filter data: {e}")


async def mandatory_filter_checks(query_params):
    # Validation checks
    mandatory_fields = {
        "releaseStream": "nightly",
        "ciSystem": "jenkins",
    }

    for key, required_value in mandatory_fields.items():
        if key in query_params and not any(
            item.lower() == required_value for item in query_params[key]
        ):
            return False

    return True


async def get_updated_filter(filter):
    if not filter:
        return ""

    query_params = get_dict_from_qs(filter)

    # Map jobStatus to result
    if "jobStatus" in query_params:
        query_params["result"] = query_params.pop("jobStatus")

    # Remove unnecessary fields
    for key in ["releaseStream", "ciSystem"]:
        query_params.pop(key, None)

    return urlencode(query_params, doseq=True) if query_params else ""
