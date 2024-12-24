from datetime import date
import pandas as pd
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService


async def getData(
    start_datetime: date,
    end_datetime: date,
    size: int,
    offset: int,
    sort: str,
    configpath: str,
):
    query = {
        "size": size,
        "from": offset,
        "query": {
            "bool": {"filter": {"range": {"timestamp": {"format": "yyyy-MM-dd"}}}}
        },
    }
    if sort:
        query["sort"] = utils.build_sort_terms(sort)

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


async def getFilterData(start_datetime: date, end_datetime: date, configpath: str):
    start_date = (
        start_datetime.strftime("%Y-%m-%d")
        if start_datetime
        else (datetime.utcnow().date() - timedelta(days=5).strftime("%Y-%m-%d"))
    )
    end_date = (
        end_datetime.strftime("%Y-%m-%d")
        if end_datetime
        else datetime.utcnow().strftime("%Y-%m-%d")
    )

    query = {
        "aggs": {
            "min_timestamp": {"min": {"field": start_date}},
            "max_timestamp": {"max": {"field": end_date}},
        },
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "format": "yyyy-MM-dd",
                                "lte": end_date,
                                "gte": start_date,
                            }
                        }
                    }
                ],
                "should": [],
                "must_not": [],
            }
        },
    }

    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery()
    query["aggs"].update(aggregate)

    response = await es.filterPost(query=query)
    await es.close()

    summary = {"total": response["total"]}

    filterData = []
    filter_ = response["filter_"]

    summary.update({x["key"]: x["doc_count"] for x in filter_["jobStatus"]["buckets"]})

    upstreamList = [x["key"] for x in filter_["upstream"]["buckets"]]
    clusterTypeList = [x["key"] for x in filter_["clusterType"]["buckets"]]
    buildList = [x["key"] for x in filter_["build"]["buckets"]]
    keys_to_remove = [
        "min_timestamp",
        "max_timestamp",
        "upstream",
        "clusterType",
        "build",
    ]
    filter_ = utils.removeKeys(filter_, keys_to_remove)

    for key, value in response["filter_"].items():
        filterObj = {"key": key, "value": []}
        buckets = value["buckets"]
        for bucket in buckets:
            filterObj["value"].append(bucket["key"])
            if key == "platform":
                platformOptions = utils.buildPlatformFilter(
                    upstreamList, clusterTypeList
                )
                filterObj["value"] += platformOptions
        filterData.append(filterObj)

    jobType = getJobType(upstreamList)
    isRehearse = getIsRehearse(upstreamList)
    build = utils.getBuildFilter(buildList)
    buildObj = {"key": "build", "value": build}
    jobTypeObj = {"key": "jobType", "value": jobType}
    isRehearseObj = {"key": "isRehearse", "value": isRehearse}

    filterData.append(jobTypeObj)
    filterData.append(buildObj)
    filterData.append(isRehearseObj)

    return {"filterData": filterData, "summary": summary}


def getJobType(upstreamList: list):
    return list(
        set(
            [
                "periodic" if "periodic" in item else "pull-request"
                for item in upstreamList
            ]
        )
    )


def getIsRehearse(upstreamList: list):
    return list(
        set(["True" if "rehearse" in item else "False" for item in upstreamList])
    )
