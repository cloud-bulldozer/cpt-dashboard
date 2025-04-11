def response_200(example):
    return {
        "content": {
            "application/json": {
                "example": example,
            }
        },
    }


def response_422():
    return {
        "content": {
            "application/json": {
                "example": {
                    "error": "invalid date format, start_date must be less than end_date"
                },
            }
        },
    }


ocp_response_example = {
    "startDate": "2023-09-20",
    "endDate": "2023-09-20",
    "results": [
        {
            "ciSystem": "PROW",
            "uuid": "CPT-e3865b03-ce78-454a-becb-b79aeb806a6b",
            "releaseStream": "4.14.0-0.nightly",
            "platform": "AWS",
            "clusterType": "self-managed",
            "benchmark": "cluster-density-v2",
            "masterNodesCount": 3,
            "workerNodesCount": 252,
            "infraNodesCount": 3,
            "masterNodesType": "m6a.8xlarge",
            "workerNodesType": "m5.2xlarge",
            "infraNodesType": "r5.4xlarge",
            "totalNodesCount": 258,
            "clusterName": "ci-op-4n0msnvp-7904a-s5sv8",
            "ocpVersion": "4.14.0-0.nightly-2023-09-15-233408",
            "networkType": "OVNKubernetes",
            "buildTag": "1704299395064795136",
            "jobStatus": "success",
            "buildUrl": "https://example.com/1704299395064795136",
            "upstreamJob": "periodic-ci-openshift",
            "upstreamJobBuild": "5fe07ad3-5415-433c-b9af-f60545d0d432",
            "executionDate": "2023-09-20T02:14:07Z",
            "jobDuration": "5261",
            "startDate": "2023-09-20T02:14:07Z",
            "endDate": "2023-09-20T03:41:48Z",
            "timestamp": "2023-09-20T02:14:07Z",
            "shortVersion": "4.14",
        },
        {
            "ciSystem": "PROW",
            "uuid": "CPT-0d58dddf-721a-4952-985e-046bc17ee3cc",
            "releaseStream": "4.13.0-0.nightly",
            "platform": "GCP",
            "clusterType": "self-managed",
            "benchmark": "node-density",
            "masterNodesCount": 3,
            "workerNodesCount": 24,
            "infraNodesCount": 3,
            "masterNodesType": "e2-standard-4",
            "workerNodesType": "e2-standard-4",
            "infraNodesType": "n1-standard-16",
            "totalNodesCount": 30,
            "clusterName": "ci-op-x2ic4nsf-8360f-kzbcg",
            "ocpVersion": "4.13.0-0.nightly-2023-09-12-074803",
            "networkType": "OVNKubernetes",
            "buildTag": "1704367060252889088",
            "jobStatus": "success",
            "buildUrl": "https://example/1704367060252889088",
            "upstreamJob": "periodic-ci-openshift",
            "upstreamJobBuild": "3ab02e3b-3000-4fc9-a30c-9cd02fe4a78c",
            "executionDate": "2023-09-20T07:19:00Z",
            "jobDuration": "582",
            "startDate": "2023-09-20T07:19:00Z",
            "endDate": "2023-09-20T07:28:42Z",
            "timestamp": "2023-09-20T07:19:00Z",
            "shortVersion": "4.13",
        },
    ],
}

quay_response_example = {
    "startDate": "2023-09-20",
    "endDate": "2023-09-20",
    "results": [
        {
            "ciSystem": "PROW",
            "uuid": "CPT-e3865b03-ce78-454a-becb-b79aeb806a6b",
            "releaseStream": "stable-3.10",
            "platform": "AWS",
            "clusterType": "self-managed",
            "benchmark": "quay-load-test",
            "hitSize": 100,
            "concurrency": 50,
            "imagePushPulls": 10,
            "masterNodesCount": 3,
            "workerNodesCount": 252,
            "infraNodesCount": 3,
            "masterNodesType": "m6a.8xlarge",
            "workerNodesType": "m5.2xlarge",
            "infraNodesType": "r5.4xlarge",
            "totalNodesCount": 258,
            "clusterName": "quaytest-123sffdf",
            "ocpVersion": "4.14.0-0.nightly-2023-09-15-233408",
            "networkType": "OVNKubernetes",
            "buildTag": "1704299395064795136",
            "jobStatus": "success",
            "buildUrl": "https://example.com/1704299395064795136",
            "upstreamJob": "quay-pipeline",
            "executionDate": "2023-09-20T02:14:07Z",
            "jobDuration": "5261",
            "startDate": "2023-09-20T02:14:07Z",
            "endDate": "2023-09-20T03:41:48Z",
            "timestamp": "2023-09-20T02:14:07Z",
            "shortVersion": "4.14",
        },
    ],
}

telco_response_example = {
    "startDate": "2023-09-20",
    "endDate": "2023-09-20",
    "results": [
        {
            "uuid": "4de79cb7a1b071bce282e8d0ce2006c7",
            "encryptedData": "gAAAAABmR0NYcO6AZo4nGjkT1IBVeoD=",
            "ciSystem": "Jenkins",
            "benchmark": "deployment",
            "shortVersion": "4.16",
            "ocpVersion": "4.16.0-0.nightly-2024-05-16-092402",
            "releaseStream": "Nightly",
            "nodeName": "kni-qe-66",
            "cpu": "Intel(R) Xeon? Gold 5423N",
            "formal": "true",
            "startDate": "2024-05-16 19:39:48+00:00",
            "endDate": "2024-05-16 20:41:48+00:00",
            "buildUrl": "https://ci-jenkins-xxx.com/job/your-tests/532",
            "jobStatus": "success",
            "jobDuration": 3720,
        },
    ],
}

ols_response_example = {
    "startDate": "2025-02-01",
    "endDate": "2025-02-07",
    "results": [    
        {
        "ciSystem": "PROW",
        "uuid": "4c28dc49-98b1-425c-a3a3-4109a1576ceb",
        "releaseStream": "4.15.0-0.nightly",
        "platform": "AWS",
        "clusterType": "self-managed",
        "benchmark": "ols-load-generator",
        "masterNodesCount": 3,
        "workerNodesCount": 3,
        "infraNodesCount": 3,
        "masterNodesType": "m6a.xlarge",
        "workerNodesType": "m6i.xlarge",
        "infraNodesType": "r5.xlarge",
        "totalNodesCount": 9,
        "clusterName": "ci-op-33k29hx2-3e7b8-l6hlg",
        "ocpVersion": "4.15.0-0.nightly-2025-02-03-164127",
        "networkType": "OVNKubernetes",
        "buildTag": "1886955825944072192",
        "jobStatus": "success",
        "buildUrl": "https://prow.ci.openshift.org/view/gs/test-platform-results/pr-logs/pull/openshift_release/60981/rehearse-60981-periodic-ci-openshift-ols-load-generator-main-ols-load-test-100workers/1886955825944072192",
        "upstreamJob": "rehearse-60981-periodic-ci-openshift-ols-load-generator-main-ols-load-test-100workers",
        "upstreamJobBuild": "778dd992-8353-4cec-9807-7343290267f8",
        "executionDate": "2025-02-05T03:19:50Z",
        "jobDuration": "3396",
        "startDate": "2025-02-05T03:19:50Z",
        "endDate": "2025-02-05T04:16:26Z",
        "startDateUnixTimestamp": "1738725590",
        "endDateUnixTimestamp": "1738728986",
        "timestamp": "2025-02-05T04:16:37Z",
        "ipsec": "false",
        "ipsecMode": "Disabled",
        "fips": "false",
        "encrypted": "false",
        "encryptionType": "None",
        "publish": "External",
        "computeArch": "amd64",
        "controlPlaneArch": "amd64",
        "olsTestWorkers": 100,
        "olsTestDuration": "5m",
        "jobType": "periodic",
        "isRehearse": "True",
        "build": "2025-02-03-164127",
        "shortVersion": "4.15"
        },
    ]
}

def ocp_200_response():
    return response_200(ocp_response_example)


def quay_200_response():
    return response_200(quay_response_example)


def telco_200_response():
    return response_200(telco_response_example)


def ols_200_response():
    return response_200(ols_response_example)


def ocp_filter_200_response():
    return response_200(ocp_filter_example)


def quay_filter_200_response():
    return response_200(quay_filter_example)


cpt_response_example = {
    "startDate": "2023-11-18",
    "endDate": "2023-11-23",
    "results": [
        {
            "ciSystem": "PROW",
            "uuid": "f6d084d5-b154-4108-b4f7-165094ccc838",
            "releaseStream": "Nightly",
            "jobStatus": "success",
            "buildUrl": "https://ci..org/view/1726571333392797696",
            "startDate": "2023-11-20T13:16:34Z",
            "endDate": "2023-11-20T13:28:48Z",
            "product": "ocp",
            "version": "4.13",
            "testName": "cluster-density-v2",
        },
        {
            "ciSystem": "JENKINS",
            "uuid": "5b729011-3b4d-4ec4-953d-6881ac9da505",
            "releaseStream": "Stable",
            "jobStatus": "success",
            "buildUrl": "https://ci..org/view/1726571333392797696",
            "startDate": "2023-11-20T13:16:30Z",
            "endDate": "2023-11-20T13:30:40Z",
            "product": "ocp",
            "version": "4.14",
            "testName": "node-density-heavy",
        },
    ],
}

ocp_filter_example = {
    "filterData": [
        {"key": "jobStatus", "value": ["success", "failure"]},
        {"key": "workerNodesCount", "value": [24, 6, 9, 3, 120, 249, 252, 25, 4, 240]},
        {"key": "jobType", "value": ["pull-request", "periodic"]},
        {"key": "isRehearse", "value": ["True", "False"]},
        {"key": "networkType", "value": ["OVNKubernetes", "OpenShiftSDN"]},
    ],
    "summary": {"total": 259, "success": 254, "failure": 5},
}

quay_filter_example = {
    "filterData": [
        {"key": "jobStatus", "value": ["success", "failure"]},
        {"key": "workerNodesCount", "value": [24]},
        {"key": "platform", "value": ["AWS"]},
        {"key": "benchmark", "value": ["quay-load-test"]},
        {
            "key": "build",
            "value": ["2024-10-12-102620"],
        },
    ],
    "summary": {"total": 3, "success": 3},
}


def cpt_200_response():
    return response_200(cpt_response_example)
