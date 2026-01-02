import ast
from collections import defaultdict
from typing import Optional
from urllib.parse import parse_qs

from fastapi import HTTPException, status

import app.api.v1.commons.constants as constants
from app.services.search import ElasticService


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
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": f"offset {offset} specified without size"},
        )
    elif not offset and not size:
        size = constants.MAX_PAGE
        offset = 0
    elif not offset:
        offset = 0
    elif offset >= constants.MAX_PAGE:
        message = (
            f"Offset {offset} is too big (>= {constants.MAX_PAGE}). "
            "Narrow the date range or select more specific filtering"
        )
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": message},
        )
    return offset, size


def buildAggregateQuery(constant_dict):
    aggregate = {}
    for x, y in constant_dict.items():
        obj = {x: {"terms": {"field": y, "size": constants.AGG_BUCKET_SIZE}}}
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


def get_dict_from_qs(qs):
    if not qs:
        return {}
    parsed_qs = parse_qs(qs)
    result = {}
    for key, values in parsed_qs.items():
        processed_values = []
        for value_str in values:
            try:
                # Safely evaluate the string if it looks like a list
                evaluated_value = ast.literal_eval(value_str)
                if isinstance(evaluated_value, (list, tuple)):
                    processed_values.extend([str(item) for item in evaluated_value])
                else:
                    processed_values.append(str(evaluated_value))
            except (SyntaxError, ValueError):

                processed_values.append(str(value_str))
        result[key] = processed_values
    return result


def construct_query(filter_dict):
    query_parts = []
    if isinstance(filter_dict, dict):
        for key, values in filter_dict.items():
            k = constants.FIELDS_FILTER_DICT[key]
            # as status values are mapped differenlty for telco
            if k == "status":
                values = [constants.TELCO_STATUS_MAP.get(val, val) for val in values]
            if key == "releaseStream":
                reverse_map = {
                    v.lower(): kf for kf, v in constants.RELEASE_STREAM_DICT.items()
                }
                values = [
                    f"*{reverse_map[val.lower()]}*"
                    for val in values
                    if val.lower() in reverse_map
                ]

            if len(values) > 1:
                or_clause = " OR ".join(f'{k}="{value}"' for value in values)
                query_parts.append(or_clause)
            else:
                query_parts.append(f'{k}="{values[0]}"')
        return " ".join(query_parts)


def create_match_phrase(key, item):
    match_phrase = {"match_phrase": {key: item}}
    return match_phrase


def invert_job_status_map():
    inverted = defaultdict(list)
    for raw, canonical in constants.JOB_STATUS_MAP.items():
        inverted[canonical].append(raw)
    return inverted


INVERTED_JOB_STATUS_MAP = invert_job_status_map()
ALL_KNOWN_JOB_STATUSES = set(constants.JOB_STATUS_MAP.keys())


def handle_job_status(values, field, should, must_not):
    min_match_inc = 0

    # Handle "others"
    if "others" in values:
        for job_status in ALL_KNOWN_JOB_STATUSES:
            must_not.append(create_match_phrase(field, job_status))

        values = [v for v in values if v != "others"]

        if not values:
            return 1  # only others selected

    # Handle success / failure
    for value in values:
        canonical = constants.JOB_STATUS_MAP.get(value, value)
        expanded = INVERTED_JOB_STATUS_MAP.get(canonical, [])

        for job_status in expanded:
            should.append(create_match_phrase(field, job_status))

        min_match_inc += 1

    return min_match_inc


def construct_ES_filter_query(filter):
    should_part = []
    must_not_part = []

    key_to_field = {
        "build": "ocpVersion",
        "jobType": "upstreamJob",
        "isRehearse": "upstreamJob",
        "product": "group",
    }

    # W.R.T jobType(job) and isRehearse(job) of the utils.py file

    # if the job contains "periodic" set `jobType` as "periodic" else "pull-request"
    # When filtering if the value is periodic it should be included in the `should_part`
    # Otherwise it should be in the `must_not_part`

    #  if the job contains "rehearse" set `isRehearse` as "True" else "false"
    #  When filtering if the value is True it should be included in the `should_part`
    #  Otherwise, it should be in the `must_not_part`

    search_value = {"isRehearse": "rehearse", "jobType": "periodic", "result": "PASS"}
    min_match = 0
    for key, values in filter.items():
        field = key_to_field.get(key, key)
        if key == "jobStatus" and "others" in values:
            for job_status in constants.JOB_STATUS_MAP.keys():
                must_not_part.append(create_match_phrase(field, job_status))
            values.remove("others")
            if not values:
                min_match += 1
                continue
        min_match += 1
        for value in values:
            if key in search_value:
                match_clause = create_match_phrase(field, search_value[key])
                if key == "isRehearse":
                    target_list = must_not_part if not value else should_part
                elif key == "jobType":
                    target_list = should_part if value == "periodic" else must_not_part
                elif key == "result":
                    target_list = must_not_part if value == "failure" else should_part
                target_list.append(match_clause)
            else:
                should_part.append(create_match_phrase(field, value))

    return {
        "query": should_part,
        "must_query": must_not_part,
        "min_match": min_match - len(must_not_part),
    }


def transform_filter(filter):
    filter_dict = get_dict_from_qs(filter)
    refiner = construct_ES_filter_query(filter_dict)
    return refiner


def update_filter_product(filter):
    filter_dict = get_dict_from_qs(filter) if filter else {}
    filter_product = filter_dict.pop("product", None)

    # The product filter dropdown includes options like "ocp", "telco", "quay",
    # "Developer", "Insights", etc
    #
    # Among these, "ocp", "quay", and "telco" are considered STANDOUT_PRODUCTS.
    # These standout products are handled through a product-to-mapper lookup,
    # so they do NOT need to be included in the filter_dict explicitly. The
    # remaining products (like "Developer", "Insights", etc.) must be filtered
    # using "hce" and "ocm" mappers, so they are retained in the filter_dict
    # for backend filtering.

    if filter_product:
        matched = [p for p in filter_product if p in constants.STANDOUT_PRODUCTS]
        unmatched = [p for p in filter_product if p not in constants.STANDOUT_PRODUCTS]
        filter_product = matched + constants.GENERAL_PRODUCTS if unmatched else matched
        filter_dict["product"] = unmatched
    return filter_product, filter_dict
