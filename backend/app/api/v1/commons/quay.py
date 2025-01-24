from datetime import date
import pandas as pd
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService
from app.api.v1.commons.constants import QUAY_FIELD_CONSTANT_DICT


async def getData(
    start_datetime: date,
    end_datetime: date,
    size,
    offset,
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

    if sort:
        query["sort"] = utils.build_sort_terms(sort)
    if filter:
        refiner = utils.transform_filter(filter)
        query["query"]["bool"]["should"] = refiner["query"]
        query["query"]["bool"]["minimum_should_match"] = refiner["min_match"]
        query["query"]["bool"]["must_not"] = refiner["must_query"]

    if filter:
        refiner = utils.transform_filter(filter)

        should.extend(refiner["query"])
        must_not.extend(refiner["must_query"])
        query["query"]["bool"]["minimum_should_match"] = refiner["min_match"]

    es = ElasticService(configpath=configpath)
    response = await es.post(
        query=query,
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
    jobs["benchmark"] = jobs.apply(utils.updateBenchmark, axis=1)
    jobs["platform"] = jobs.apply(utils.clasifyAWSJobs, axis=1)
    jobs["jobStatus"] = jobs.apply(utils.updateStatus, axis=1)
    jobs["build"] = jobs.apply(utils.getBuild, axis=1)
    jobs["shortVersion"] = jobs["ocpVersion"].str.slice(0, 4)

    cleanJobs = jobs[jobs["platform"] != ""]

    return {"data": cleanJobs, "total": response["total"]}


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):

    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(QUAY_FIELD_CONSTANT_DICT)
    refiner = ""
    if filter:
        refiner = utils.transform_filter(filter)

    response = await es.filterPost(start_datetime, end_datetime, aggregate, refiner)
    await es.close()

    return {"filterData": response["filterData"], "summary": response["summary"]}
