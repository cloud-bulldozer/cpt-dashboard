from datetime import date

import pandas as pd

from app.api.v1.commons.constants import OCP_FIELD_CONSTANT_DICT
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
    sort: str,
    filter: str,
    configpath: str,
):
    should = []
    must_not = []
    query = {
        "size": size,
        "from": offset,
        "query": {
            "bool": {
                "filter": {"range": {"timestamp": {"format": "yyyy-MM-dd"}}},
                "should": should,
                "must_not": must_not,
            }
        },
    }
    if sort is not None:
        query["sort"] = utils.build_sort_terms(sort)

    if filter:
        refiner = utils.transform_filter(filter)

        should.extend(refiner["query"])
        must_not.extend(refiner["must_query"])
        query["query"]["bool"]["minimum_should_match"] = refiner["min_match"]

    es = ElasticService(configpath=configpath)
    response = await es.post(
        query=query,
        size=size,
        start_date=start_datetime,
        end_date=end_datetime,
        timestamp_field="timestamp",
    )
    await es.close()
    tasks = [item["_source"] for item in response["data"]]
    jobs = pd.json_normalize(tasks)
    if len(jobs) == 0:
        return {"data": jobs, "total": response["total"]}

    jobs[
        ["masterNodesCount", "workerNodesCount", "infraNodesCount", "totalNodesCount"]
    ] = jobs[
        ["masterNodesCount", "workerNodesCount", "infraNodesCount", "totalNodesCount"]
    ].fillna(
        0
    )
    jobs.fillna("", inplace=True)
    jobs[
        ["ipsec", "fips", "encrypted", "publish", "computeArch", "controlPlaneArch"]
    ] = jobs[
        ["ipsec", "fips", "encrypted", "publish", "computeArch", "controlPlaneArch"]
    ].replace(
        r"^\s*$", "N/A", regex=True
    )
    jobs["encryptionType"] = jobs.apply(fillEncryptionType, axis=1)
    jobs["benchmark"] = jobs.apply(utils.updateBenchmark, axis=1)
    jobs["platform"] = jobs.apply(utils.clasifyAWSJobs, axis=1)
    jobs["jobType"] = jobs.apply(utils.jobType, axis=1)
    jobs["isRehearse"] = jobs.apply(utils.isRehearse, axis=1)
    jobs["jobStatus"] = jobs.apply(utils.updateStatus, axis=1)
    jobs["build"] = jobs.apply(utils.getBuild, axis=1)

    cleanJobs = jobs[jobs["platform"] != ""]

    jbs = cleanJobs
    jbs["shortVersion"] = jbs["ocpVersion"].str.slice(0, 4)

    return {"data": jbs, "total": response["total"]}


def fillEncryptionType(row):
    if row["encrypted"] == "N/A":
        return "N/A"
    elif row["encrypted"] == "false":
        return "None"
    else:
        return row["encryptionType"]


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):
    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(OCP_FIELD_CONSTANT_DICT)
    refiner = utils.transform_filter(filter) if filter else ""

    response = await es.filterPost(start_datetime, end_datetime, aggregate, refiner)
    await es.close()

    if not response.get("filterData", []) or response.get("total", 0) == 0:
        return {"total": response.get("total", 0), "filterData": [], "summary": {}}

    upstreamList = response.get("upstreamList", [])

    jobType = getJobType(upstreamList)
    isRehearse = getIsRehearse(upstreamList)

    jobTypeObj = {
        "key": "jobType",
        "value": jobType,
        "name": "Job Type",
    }
    isRehearseObj = {"key": "isRehearse", "value": isRehearse, "name": "Rehearse"}

    response["filterData"].append(jobTypeObj)
    response["filterData"].append(isRehearseObj)

    return {
        "filterData": response.get("filterData", []),
        "summary": response.get("summary", {}),
        "total": response.get("total", 0),
    }


def getJobType(upstreamList: list):
    return list(
        {"periodic" if "periodic" in item else "pull-request" for item in upstreamList}
    )


def getIsRehearse(upstreamList: list):
    return list({"True" if "rehearse" in item else "False" for item in upstreamList})
