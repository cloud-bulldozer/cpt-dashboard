import json
from fastapi import Response
from datetime import datetime, timedelta, date
from fastapi import APIRouter
from ...commons.ocp import getData
from fastapi.param_functions import Query

router = APIRouter()

response_example ={
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

unprocessable_example = {"error": "invalid date format, start_date must be less than end_date"}

@router.get('/api/ocp/v1/jobs',
            summary="Returns a job list",
            description="Returns a list of jobs in the specified dates. \
            If not dates are provided the API will default the values. \
            `startDate`: will be set to the day of the request minus 5 days.\
            `endDate`: will be set to the day of the request.",
            responses={
            200: {
                "content": {
                    "application/json": {
                        "example": response_example,
                    }
                },
            },
            422: {
                "content": {
                    "application/json": {
                        "example": unprocessable_example
                    }
                }
            }
        },)
async def jobs(start_date: date = Query(None, description="Start date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-10"]),
                end_date: date = Query(None, description="End date for searching jobs, format: 'YYYY-MM-DD'", examples=["2020-11-15"]),
                pretty: bool = Query(False, description="Output contet in pretty format.")):
    if start_date is None:
        start_date = datetime.utcnow().date()
        start_date = start_date - timedelta(days=5)

    if end_date is None:
        end_date = datetime.utcnow().date()

    if start_date > end_date:
        return Response(content=json.dumps({'error': "invalid date format, start_date must be less than end_date"}), status_code=422)

    results = await getData(start_date, end_date)

    response = {
        'startDate': start_date.__str__(),
        'endDate': end_date.__str__(),
        'results': results.to_dict('records')
    }

    if pretty:
        json_str = json.dumps(response, indent=4)
        return Response(content=json_str, media_type='application/json')

    jsonstring = json.dumps(response)
    return jsonstring
