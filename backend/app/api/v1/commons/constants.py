# Define the keywords for sorting.
# numeric fields are without .keyword
DIRECTIONS = ("asc", "desc")
FIELDS = (
    "ciSystem.keyword",
    "benchmark.keyword",
    "ocpVersion.keyword",
    "releaseStream.keyword",
    "platform.keyword",
    "networkType.keyword",
    "ipsec.keyword",
    "fips.keyword",
    "encrypted.keyword",
    "publish.keyword",
    "computeArch.keyword",
    "controlPlaneArch.keyword",
    "jobStatus.keyword",
    "startDate",
    "endDate",
    "workerNodesCount",
    "masterNodesCount",
    "infraNodesCount",
    "totalNodesCount",
)
MAX_PAGE = 10000
OCP_SHORT_VER_LEN = 6

OCP_FIELD_CONSTANT_DICT = {
    "ciSystem": "ciSystem.keyword",
    "platform": "platform.keyword",
    "benchmark": "benchmark.keyword",
    "releaseStream": "releaseStream.keyword",
    "networkType": "networkType.keyword",
    "workerNodesCount": "workerNodesCount",
    "jobStatus": "jobStatus.keyword",
    "controlPlaneArch": "controlPlaneArch.keyword",
    "publish": "publish.keyword",
    "fips": "fips.keyword",
    "encrypted": "encrypted.keyword",
    "ipsec": "ipsec.keyword",
    "ocpVersion": "ocpVersion.keyword",
    "build": "ocpVersion.keyword",
    "upstream": "upstreamJob.keyword",
    "clusterType": "clusterType.keyword",
}

QUAY_FIELD_CONSTANT_DICT = {
    "benchmark": "benchmark.keyword",
    "platform": "platform.keyword",
    "releaseStream": "releaseStream.keyword",
    "workerNodesCount": "workerNodesCount",
    "jobStatus": "jobStatus.keyword",
    "build": "ocpVersion.keyword",
    "upstream": "upstreamJob.keyword",
    "clusterType": "clusterType.keyword",
}

RELEASE_STREAM_DICT = {
    "fast": "Fast",
    "stable": "Stable",
    "eus": "EUS",
    "candidate": "Release Candidate",
    "rc": "Release Candidate",
    "nightly": "Nightly",
    "ci": "ci",
    "ec": "Engineering Candidate",
}

TELCO_FIELDS_DICT = {
    "cpu": "CPU",
    "benchmark": "Benchmark",
    "releaseStream": "Release Stream",
    "nodeName": "Node Name",
    "startDate": "Start Date",
    "endDate": "End Date",
    "jobStatus": "Status",
    "ocpVersion": "Build",
}

FILEDS_DISPLAY_NAMES = {
    "ciSystem": "CI System",
    "platform": "Platform",
    "benchmark": "Benchmark",
    "releaseStream": "Release Stream",
    "networkType": "Network Type",
    "workerNodesCount": "Worker Count",
    "jobStatus": "Status",
    "controlPlaneArch": "Control Plane Architecture",
    "publish": "Control Plane Access",
    "fips": "FIPS Enabled",
    "encrypted": "Is Encrypted",
    "ipsec": "Has IPSEC",
    "ocpVersion": "Versions",
    "build": "Build",
    "computeArch": "Compute Architecture",
    "jobStatus": "Status",
    "startDate": "Start Date",
    "endDate": "End Date",
    "result": "Status",
    "product": "Product",
    "testName": "Test Name",
    "attack": "Test Name",
}

FIELDS_FILTER_DICT = {
    "nodeName": "node_name",
    "cpu": "cpu",
    "benchmark": "test_type",
    "ocpVersion": "ocp_version",
    "releaseStream": "ocp_build",
}

HCE_FIELD_CONSTANT_DICT = {
    "testName": "test.keyword",
    "product": "group.keyword",
    "result": "result.keyword",
}

OCM_FIELD_CONSTANT_DICT = {
    "jobStatus": "jobStatus.keyword",
    "testName": "attack.keyword",
    "ciSystem": "ciSystem.keyword",
}

JOB_STATUS_MAP = {
    "pass": "success",
    "fail": "failure",
    "success": "success",
    "failure": "failure",
    "error": "failure",
}

keys_to_keep = ["product", "testName", "jobStatus", "ciSystem", "releaseStream"]
