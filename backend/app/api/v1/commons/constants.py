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
    "nodeName",
    "cpu",
    "benchmark",
    "ocpVersion",
    "jobStatus",
    "formal",
    "ciSystem",
)
AGG_BUCKET_SIZE = 1000
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

OLS_FIELD_CONSTANT_DICT = {
    "benchmark": "benchmark.keyword",
    "releaseStream": "releaseStream.keyword",
    "platform": "platform.keyword",
    "workerNodesCount": "workerNodesCount",
    "olsTestWorkers": "olsTestWorkers",
    "olsTestDuration": "olsTestDuration.keyword",
    "jobStatus": "jobStatus.keyword",
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
    "ciSystem": "ciSystem.keyword",
    "imagePushPulls": "imagePushPulls",
    "concurrency": "concurrency",
    "hitSize": "hitSize",
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
    "isFormal": "Formal",
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
    "concurrency": "Concurrency",
    "imagePushPulls": "Image Push/Pulls",
    "olsTestWorkers": "Parallel Users",
    "olsTestDuration": "Load Duration",
    "hitSize": "Hit Size",
    "isFormal": "Is Formal",
}

FIELDS_FILTER_DICT = {
    "nodeName": "node_name",
    "cpu": "cpu",
    "benchmark": "test_type",
    "ocpVersion": "ocp_version",
    "releaseStream": "ocp_build",
    "jobStatus": "status",
    "endDate": "_indextime",
    "startDate": "_indextime",
    "formal": "isFormal",
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

OSO_FIELD_CONSTANT_DICT = {
    "ciSystem": "ciSystem.keyword",
    "networkType": "networkType.keyword",
    "jobStatus": "jobStatus.keyword",
    "ocpVersion": "ocpVersion.keyword",
    "build": "ocpVersion.keyword",
}

JOB_STATUS_MAP = {
    "pass": "success",
    "fail": "failure",
    "success": "success",
    "failure": "failure",
    "error": "failure",
    "passed": "success",
    "failed": "failure",
}

JOB_STATUS_OTHERS = "others"

keys_to_keep = ["product", "testName", "jobStatus", "ciSystem", "releaseStream"]

SPLUNK_SEMAPHORE_COUNT = 5  # Arbitrary concurrency limit in an asyncio semaphore

# These products don't need to be included in the filter dict when applying
# filters on the Home tab, as the filtering function will automatically handle
# them using the corresponding product-to-mapper lookup.
STANDOUT_PRODUCTS = ["ocp", "telco", "quay"]
# These products aren't listed by their exact names like "hce" and "ocm",
# but instead represent grouped categories such as "Developer" or "Insights".
GENERAL_PRODUCTS = ["hce", "ocm"]
TELCO_STATUS_MAP = {"success": "passed", "failed": "failed", "failure": "failure"}

REVERSE_RELEASE_STREAM_MAP = {v.lower(): kf for kf, v in RELEASE_STREAM_DICT.items()}
