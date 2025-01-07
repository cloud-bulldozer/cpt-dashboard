from app.services.search import ElasticService

from fastapi import HTTPException, status
import re
import app.api.v1.commons.constants as constants
from typing import Optional


async def getMetadata(uuid: str, configpath: str):
    query = {"query": {"query_string": {"query": (f'uuid: "{uuid}"')}}}
    print(query)
    es = ElasticService(configpath=configpath)
    response = await es.post(query=query)
    await es.close()
    meta = [item["_source"] for item in response["data"]]
    return meta[0]


def updateStatus(job):
    return job["jobStatus"].lower()


def updateBenchmark(job):
    if job["upstreamJob"].__contains__("upgrade"):
        return "upgrade-" + job["benchmark"]
    return job["benchmark"]


def jobType(job):
    if job["upstreamJob"].__contains__("periodic"):
        return "periodic"
    return "pull request"


def isRehearse(job):
    if job["upstreamJob"].__contains__("rehearse"):
        return "True"
    return "False"


def clasifyAWSJobs(job):
    if ("rosa-hcp" in job["clusterType"]) or (
        "rosa" in job["clusterType"]
        and job["masterNodesCount"] == 0
        and job["infraNodesCount"] == 0
    ):
        return "AWS ROSA-HCP"
    if job["clusterType"].__contains__("rosa"):
        return "AWS ROSA"
    return job["platform"]


def getBuild(job):
    releaseStream = job["releaseStream"] + "-"
    ocpVersion = job["ocpVersion"]
    return ocpVersion.replace(releaseStream, "")


def getReleaseStream(row):
    releaseStream = next(
        (
            v
            for k, v in constants.RELEASE_STREAM_DICT.items()
            if k in row["releaseStream"]
        ),
        "Stable",
    )
    return releaseStream


def build_sort_terms(sort_string: str) -> list[dict[str, str]]:
    """

    Validates and transforms a sort string in the format 'sort=key:direction' to
    a list of dictionaries [{key: {"order": direction}}].

    :param sort_string: str, input string in the format 'sort=key:direction'

    :return: list, transformed sort structure or raises a ValueError for invalid input

    """
    sort_terms = []
    if sort_string:
        key, dir = sort_string.split(":", maxsplit=1)
        if dir not in constants.DIRECTIONS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Sort direction {dir!r} must be one of {','.join(constants.DIRECTIONS)}",
            )
        if key not in constants.FIELDS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Sort key {key!r} must be one of {','.join(constants.FIELDS)}",
            )
        sort_terms.append({f"{key}": {"order": dir}})
    return sort_terms


def normalize_pagination(offset: Optional[int], size: Optional[int]) -> tuple[int, int]:
    if offset and not size:
        raise HTTPException(400, f"offset {offset} specified without size")
    elif not offset and not size:
        size = constants.MAX_PAGE
        offset = 0
    elif not offset:
        offset = 0
    elif offset >= constants.MAX_PAGE:
        raise HTTPException(
            400, f"offset {offset} is too big (>= {constants.MAX_PAGE})"
        )
    return offset, size


def buildAggregateQuery(constant_dict):
    aggregate = {}
    for x, y in constant_dict.items():
        obj = {x: {"terms": {"field": y}}}
        aggregate.update(obj)
    return aggregate


def buildReleaseStreamFilter(input_array):
    mapped_array = []
    for item in input_array:
        # Find the first matching key in the map
        match = next(
            (
                value
                for key, value in constants.RELEASE_STREAM_DICT.items()
                if key in item
            ),
            "Stable",
        )
        mapped_array.append(match)
    return list(set(mapped_array))
