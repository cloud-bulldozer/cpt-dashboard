from datetime import date
import pandas as pd
from app import config
from app.services.splunk import SplunkService
import app.api.v1.commons.hasher as hasher
from datetime import datetime, timezone
import app.api.v1.commons.utils as utils
import app.api.v1.endpoints.telco.telcoGraphs as telcoGraphs
import app.api.v1.commons.constants as constants


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
    filter: str,
    configpath: str,
):
    cfg = config.get_config()
    try:
        jenkins_url = cfg.get("telco.config.job_url")
    except Exception as e:
        print(f"Error reading telco configuration: {e}")
    test_type_execution_times = {
        "oslat": 3720,
        "cyclictest": 3720,
        "cpu_util": 6600,
        "deployment": 3720,
        "ptp": 4200,
        "reboot": 1980,
        "rfc-2544": 5580,
    }
    query = {
        "earliest_time": "{}T00:00:00".format(start_datetime.strftime("%Y-%m-%d")),
        "latest_time": "{}T23:59:59".format(end_datetime.strftime("%Y-%m-%d")),
        "output_mode": "json",
    }
    searchList = constructFilterQuery(filter)

    splunk = SplunkService(configpath=configpath)
    response = await splunk.query(
        query=query, size=size, offset=offset, searchList=searchList
    )
    mapped_list = []
    if response:
        for each_response in response["data"]:
            end_timestamp = int(each_response["timestamp"])
            test_data = each_response["data"]
            hash_digest, encrypted_data = hasher.hash_encrypt_json(each_response)
            execution_time_seconds = test_type_execution_times.get(
                test_data["test_type"], 0
            )
            start_timestamp = end_timestamp - execution_time_seconds
            start_time_utc = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
            end_time_utc = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
            kernel = test_data["kernel"] if "kernel" in test_data else "Undefined"

            mapped_list.append(
                {
                    "uuid": hash_digest,
                    "encryptedData": encrypted_data.decode("utf-8"),
                    "ciSystem": "Jenkins",
                    "benchmark": test_data["test_type"],
                    "kernel": kernel,
                    "shortVersion": test_data["ocp_version"],
                    "ocpVersion": test_data["ocp_build"],
                    "releaseStream": utils.getReleaseStream(
                        {"releaseStream": test_data["ocp_build"]}
                    ),
                    "nodeName": test_data["node_name"],
                    "cpu": test_data["cpu"],
                    "formal": test_data["formal"],
                    "startDate": str(start_time_utc),
                    "endDate": str(end_time_utc),
                    "buildUrl": jenkins_url
                    + "/"
                    + str(test_data["cluster_artifacts"]["ref"]["jenkins_build"]),
                    "jobStatus": constants.JOB_STATUS_MAP.get(
                        test_data["status"], "failure"
                    ),
                    "jobDuration": execution_time_seconds,
                }
            )

    jobs = pd.json_normalize(mapped_list)

    return {"data": jobs, "total": response["total"] if response else 0}


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):

    cfg = config.get_config()
    try:
        jenkins_url = cfg.get("telco.config.job_url")
    except Exception as e:
        print(f"Error reading telco configuration: {e}")

    query = {
        "earliest_time": "{}T00:00:00".format(start_datetime.strftime("%Y-%m-%d")),
        "latest_time": "{}T23:59:59".format(end_datetime.strftime("%Y-%m-%d")),
        "output_mode": "json",
    }
    searchList = constructFilterQuery(filter)

    splunk = SplunkService(configpath=configpath)
    response = await splunk.filterPost(query=query, searchList=searchList)
    filterData = []
    if len(response["data"]) > 0:
        for item in response["data"]:
            for field, value in item.items():
                if (
                    field == "total_records"
                    or field == "total"
                    or field == "pass_count"
                    or field == "fail_count"
                ):
                    continue

                # Determine the appropriate value transformation
                if isinstance(value, str):
                    v = [value] if value else []
                elif not isinstance(value, list):
                    v = [value]
                else:
                    v = value

                # Build the dictionary for the current field
                transformed_value = (
                    utils.buildReleaseStreamFilter(value)
                    if field == "releaseStream"
                    else v
                )

                currDict = {
                    "key": field,
                    "value": transformed_value,
                    "name": constants.TELCO_FIELDS_DICT.get(field, "Unknown Field"),
                }

                # Append the dictionary to filterData
                filterData.append(currDict)

    status_values = [
        status
        for status in ["success", "failure"]
        if response["summary"].get(status, 0) != 0
    ]

    extra_filters = [
        {"key": "jobStatus", "value": status_values, "name": "Status"},
        {"key": "ciSystem", "value": ["JENKINS"], "name": "CI System"},
    ]
    filterData.extend(extra_filters)
    return {
        "data": filterData,
        "summary": response["summary"],
        "total": response["total"],
    }


def constructFilterQuery(filter):
    test_types = [
        "oslat",
        "cyclictest",
        "cpu_util",
        "deployment",
        "ptp",
        "reboot",
        "rfc-2544",
    ]
    test_type_filter = " OR ".join(
        f'test_type="{test_type}"' for test_type in test_types
    )
    search_list = test_type_filter

    if filter:
        filter_dict = utils.get_dict_from_qs(filter)
        search_query = utils.construct_query(filter_dict)

        # Update `search_list` based on the presence of "benchmark" in `filter_dict`
        search_list = (
            search_query
            if "benchmark" in filter_dict
            else f"{search_query} {test_type_filter}"
        )
    return search_list
