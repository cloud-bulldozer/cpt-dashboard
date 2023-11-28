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
                        "example": {"error": "invalid date format, start_date must be less than end_date"},
                    }
                },
            }

ocp_response_example ={
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
            "shortVersion": "4.14"
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
            "shortVersion": "4.13"
        },
    ]
}

def ocp_200_response():
    return response_200(ocp_response_example)

cpt_response_example ={
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
        "testName": "cluster-density-v2"
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
        "testName": "node-density-heavy"
        },
    ]
}

def cpt_200_response():
    return response_200(cpt_response_example)
