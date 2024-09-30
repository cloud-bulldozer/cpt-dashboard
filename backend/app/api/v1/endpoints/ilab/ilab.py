"""Access RHEL AI InstructLab performance data through Crucible

This defines an API to expose and filter performance data from InstructLab
CPT runs via a persistent Crucuble controller instance as defined in the
configuration path "ilab.crucible".
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Query

from app.services.crucible_svc import CrucibleService, Graph, GraphList

router = APIRouter()


CONFIGPATH = "ilab.crucible"


def example_response(response) -> dict[str, Any]:
    return {"content": {"application/json": {"example": response}}}


def example_error(message: str) -> dict[str, Any]:
    return example_response({"message": message})


@router.get(
    "/api/v1/ilab/runs/filters",
    summary="Returns possible filters",
    description=(
        "Returns a nested JSON object with all parameter and tag filter terms"
    ),
    responses={
        200: example_response(
            {
                "param": {
                    "model": [
                        "/home/models/granite-7b-redhat-lab",
                        "/home/models/granite-7b-lab/",
                        "/home/models/Mixtral-8x7B-Instruct-v0.1",
                    ],
                    "gpus": ["4"],
                    "workflow": ["train", "sdg", "train+eval"],
                    "data-path": [
                        "/home/data/training/jun12-phase05.jsonl",
                        "/home/data/training/knowledge_data.jsonl",
                        "/home/data/training/jul19-knowledge-26k.jsonl",
                        "/home/data/jun12-phase05.jsonl",
                    ],
                    "nnodes": ["1"],
                    "train-until": ["checkpoint:1", "complete"],
                    "save-samples": ["5000", "2500", "10000"],
                    "deepspeed-cpu-offload-optimizer": ["0", "1"],
                    "deepspeed-cpu-offload-optimizer-pin-memory": ["0", "1"],
                    "batch-size": ["4", "8", "16", "12", "0"],
                    "cpu-offload-optimizer": ["1"],
                    "cpu-offload-pin-memory": ["1"],
                    "nproc-per-node": ["4"],
                    "num-runavg-samples": ["2", "6"],
                    "num-cpus": ["30"],
                },
                "tag": {"topology": ["none"]},
            }
        )
    },
)
async def run_filters():
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_run_filters()


@router.get(
    "/api/v1/ilab/runs",
    summary="Returns a list of InstructLab runs",
    description="Returns a list of runs summary documents.",
    responses={
        200: example_response(
            {
                "results": [
                    {
                        "benchmark": "ilab",
                        "email": "rhel-ai-user@example.com",
                        "id": "bd72561c-cc20-400b-b6f6-d9534a60033a",
                        "name": '"RHEL-AI User"',
                        "source": "n42-h01-b01-mx750c.example.com//var/lib/crucible/run/ilab--2024-09-11_19:43:53_UTC--bd72561c-cc20-400b-b6f6-d9534a60033a",
                        "status": "pass",
                        "begin_date": "1970-01-01 00:00:00+00:00",
                        "end_date": "1970-01-01 00:00:00+00:00",
                        "params": {
                            "gpus": "4",
                            "model": "/home/models/Mixtral-8x7B-Instruct-v0.1",
                            "workflow": "sdg",
                        },
                        "iterations": [
                            {
                                "iteration": 1,
                                "primary_metric": "ilab::sdg-samples-sec",
                                "primary_period": "measurement",
                                "status": "pass",
                                "params": {
                                    "gpus": "4",
                                    "model": "/home/models/Mixtral-8x7B-Instruct-v0.1",
                                    "workflow": "sdg",
                                },
                            }
                        ],
                        "primary_metrics": ["ilab::sdg-samples-sec"],
                        "tags": {"topology": "none"},
                    }
                ],
                "count": 5,
                "total": 21,
                "startDate": "2024-08-19 20:42:52.239000+00:00",
                "endDate": "2024-09-18 20:42:52.239000+00:00",
            }
        ),
        400: example_error(
            "sort key 'bad' must be one of begin,benchmark,email,end,id,name,source,status"
        ),
        422: example_error(
            "invalid date format, start_date must be less than end_date"
        ),
    },
)
async def runs(
    start_date: Annotated[
        Optional[str],
        Query(description="Start time for search", examples=["2020-11-10"]),
    ] = None,
    end_date: Annotated[
        Optional[str],
        Query(description="End time for search", examples=["2020-11-10"]),
    ] = None,
    filter: Annotated[
        Optional[list[str]],
        Query(
            description="Filter terms", examples=["tag:name=value", "param:name=value"]
        ),
    ] = None,
    sort: Annotated[
        Optional[list[str]],
        Query(description="Sort terms", examples=["start:asc", "status:desc"]),
    ] = None,
    size: Annotated[
        Optional[int], Query(description="Number of runs in a page", examples=[10])
    ] = None,
    offset: Annotated[
        int,
        Query(description="Page offset to start", examples=[10]),
    ] = 0,
):
    crucible = CrucibleService(CONFIGPATH)
    if start_date is None and end_date is None:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)
        end = now
    else:
        start = start_date
        end = end_date
    results: dict[str, Any] = crucible.get_runs(
        start=start, end=end, filter=filter, sort=sort, size=size, offset=offset
    )
    return results


@router.get(
    "/api/v1/ilab/runs/{run}/tags",
    summary="Returns the Crucible tags for a run",
    description="Returns tags for a specified Run ID.",
    responses={
        200: example_response({"topology": "none"}),
        400: example_error("Parameter error"),
    },
)
async def tags(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_tags(run)


@router.get(
    "/api/v1/ilab/runs/{run}/params",
    summary="Returns the InstructLab parameters for a run",
    description="Returns params for a specified Run ID by iteration plus common params.",
    responses={
        200: example_response(
            {
                "9D5AB7D6-510A-11EF-84ED-CCA69E6B5B5B": {
                    "num-runavg-samples": "2",
                    "cpu-offload-pin-memory": "1",
                    "nnodes": "1",
                    "cpu-offload-optimizer": "1",
                    "data-path": "/home/data/training/knowledge_data.jsonl",
                    "model": "/home/models/granite-7b-lab/",
                    "nproc-per-node": "4",
                },
                "common": {
                    "num-runavg-samples": "2",
                    "cpu-offload-pin-memory": "1",
                    "nnodes": "1",
                    "cpu-offload-optimizer": "1",
                    "data-path": "/home/data/training/knowledge_data.jsonl",
                    "model": "/home/models/granite-7b-lab/",
                    "nproc-per-node": "4",
                },
            }
        ),
        400: example_error("Parameter error"),
    },
)
async def params(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_params(run)


@router.get(
    "/api/v1/ilab/runs/{run}/iterations",
    summary="Returns a list of InstructLab run iterations",
    description="Returns a list of iterations for a specified Run ID.",
    responses={
        200: example_response(
            [
                {
                    "id": "6B98F650-7139-11EF-BB69-98B53E962BD1",
                    "num": 2,
                    "path": None,
                    "primary-metric": "ilab::sdg-samples-sec",
                    "primary-period": "measurement",
                    "status": "pass",
                },
                {
                    "id": "6B99173E-7139-11EF-9434-F8BB3B1B9CFC",
                    "num": 5,
                    "path": None,
                    "primary-metric": "ilab::sdg-samples-sec",
                    "primary-period": "measurement",
                    "status": "pass",
                },
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def iterations(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_iterations(run)


@router.get(
    "/api/v1/ilab/runs/{run}/samples",
    summary="Returns a list of InstructLab run samples",
    description="Returns a list of samples for a specified Run ID.",
    responses={
        200: example_response(
            [
                {
                    "id": "6BA5071A-7139-11EF-9864-EA6BC0BEFE10",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                },
                {
                    "id": "6BBE6872-7139-11EF-BFAA-8569A9399D61",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                },
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def run_samples(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_samples(run)


@router.get(
    "/api/v1/ilab/runs/{run}/periods",
    summary="Returns a list of InstructLab run periods",
    description="Returns a list of periods for a specified Run ID.",
    responses={
        200: example_response(
            [
                {
                    "begin": "2024-09-12 17:40:27.982000+00:00",
                    "end": "2024-09-12 18:03:23.132000+00:00",
                    "id": "6BA57EF2-7139-11EF-A80B-E5037504B9B1",
                    "name": "measurement",
                },
                {
                    "begin": "2024-09-12 16:50:19.305000+00:00",
                    "end": "2024-09-12 17:14:04.475000+00:00",
                    "id": "6BAD466E-7139-11EF-8E60-927A210BA97E",
                    "name": "measurement",
                },
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def run_periods(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_periods(run)


@router.get(
    "/api/v1/ilab/iterations/{iteration}/samples",
    summary="Returns a list of InstructLab iteration samples",
    description="Returns a list of iterations for a specified iteration ID.",
    responses={
        200: example_response(
            [
                {
                    "id": "6BB8BD00-7139-11EF-B2B2-942D604C0B7B",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                }
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def iteration_samples(iteration: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_samples(iteration=iteration)


@router.get(
    "/api/v1/ilab/runs/{run}/timeline",
    summary="Returns the 'timeline' of a run",
    description="Describes the sequence of iterations, samples, and periods.",
    responses={
        200: example_response(
            {
                "run": {
                    "id": "70d3b53f-c588-49a3-91c2-7fcf3927be7e",
                    "iterations": [
                        {
                            "id": "BFC16DA6-60C8-11EF-AB10-CF940109872B",
                            "num": 1,
                            "path": None,
                            "primary-metric": "ilab::train-samples-sec",
                            "primary-period": "measurement",
                            "status": "pass",
                            "samples": [
                                {
                                    "id": "C021BECC-60C8-11EF-A619-E0BC70D6C320",
                                    "num": "1",
                                    "path": None,
                                    "status": "pass",
                                    "periods": [
                                        {
                                            "begin": "2024-08-22 19:09:08.642000+00:00",
                                            "end": "2024-08-22 20:04:32.889000+00:00",
                                            "id": "C022CDC6-60C8-11EF-BA80-AFE7B4B2692B",
                                            "name": "measurement",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                    "begin": "2024-08-22 19:09:08.642000+00:00",
                    "end": "2024-08-22 20:04:32.889000+00:00",
                }
            }
        ),
        400: example_error("Parameter error"),
    },
)
async def timeline(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_timeline(run)


@router.get(
    "/api/v1/ilab/runs/{run}/metrics",
    summary="Describe the metrics collected for a run",
    description="Returns metric labels along with breakout names and values.",
    responses={
        200: example_response(
            {
                "ilab::train-samples-sec": {
                    "periods": ["C022CDC6-60C8-11EF-BA80-AFE7B4B2692B"],
                    "breakouts": {
                        "benchmark-group": ["unknown"],
                        "benchmark-name": ["unknown"],
                        "benchmark-role": ["client"],
                        "csid": ["1"],
                        "cstype": ["client"],
                        "endpoint-label": ["remotehosts-1"],
                        "engine-id": ["1"],
                        "engine-role": ["benchmarker"],
                        "engine-type": ["client"],
                        "hosted-by": ["nvd-srv-29.nvidia.eng.rdu2.dc.redhat.com"],
                        "hostname": ["nvd-srv-29.nvidia.eng.rdu2.dc.redhat.com"],
                        "hypervisor-host": ["none"],
                        "osruntime": ["podman"],
                        "tool-name": ["unknown"],
                        "userenv": ["rhel-ai"],
                    },
                }
            },
        ),
        400: example_error("Parameter error"),
    },
)
async def metrics(run: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metrics_list(run)


@router.get(
    "/api/v1/ilab/runs/{run}/breakouts/{metric}",
    summary="Returns breakout options for a metric",
    description="Describes the breakout names and available values for a run.",
    responses={
        200: example_response(
            {
                "label": "mpstat::Busy-CPU",
                "class": ["throughput"],
                "type": "Busy-CPU",
                "source": "mpstat",
                "breakouts": {"num": ["8", "72"], "thread": [0, 1]},
            }
        ),
        400: example_error("Metric name <name> not found for run <id>"),
    },
)
async def metric_breakouts(
    run: str,
    metric: str,
    name: Annotated[
        Optional[list[str]],
        Query(
            description="List of name[=key] to match",
            examples=["cpu=10", "cpu=10,cpu=110"],
        ),
    ] = None,
    period: Annotated[
        Optional[list[str]],
        Query(
            description="List of periods to match",
            examples=["<id>", "<id1>,<id2>"],
        ),
    ] = None,
):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metric_breakouts(run, metric, names=name, periods=period)


@router.get(
    "/api/v1/ilab/runs/{run}/data/{metric}",
    summary="Returns metric data collected for a run",
    description="Returns data collected for a specified Run ID metric.",
    responses={
        200: example_response(
            [
                {
                    "begin": "2024-08-22 20:04:05.072000+00:00",
                    "end": "2024-08-22 20:04:19.126000+00:00",
                    "duration": 14.055,
                    "value": 9.389257233311497,
                },
                {
                    "begin": "2024-08-22 20:04:19.127000+00:00",
                    "end": "2024-08-22 20:04:32.889000+00:00",
                    "duration": 13.763,
                    "value": 9.552584444155011,
                },
            ]
        ),
        400: example_error("No matches for ilab::train-samples-sc+cpu=10"),
        422: example_response(
            response={
                "detail": [
                    {
                        "message": "More than one metric (2) probably means you should add filters",
                        "names": {"dev": ["sdb", "sdb3"]},
                        "periods": [],
                    }
                ]
            }
        ),
    },
)
async def metric_data(
    run: str,
    metric: str,
    name: Annotated[
        Optional[list[str]],
        Query(
            description="List of name[=key] to match",
            examples=["cpu=10", "cpu=10,cpu=110"],
        ),
    ] = None,
    period: Annotated[
        Optional[list[str]],
        Query(
            description="List of periods to match",
            examples=["<id>", "<id1>,<id2>"],
        ),
    ] = None,
    aggregate: Annotated[
        bool, Query(description="Allow aggregation of metrics")
    ] = False,
):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metrics_data(
        run, metric, names=name, periods=period, aggregate=aggregate
    )


@router.get(
    "/api/v1/ilab/runs/{run}/summary/{metric}",
    summary="Returns metric data collected for a run",
    description="Returns data collected for a specified Run ID metric.",
    responses={
        200: example_response(
            {
                "count": 234,
                "min": 7.905045031896648,
                "max": 9.666444615077308,
                "avg": 9.38298722585416,
                "sum": 2195.6190108498736,
            }
        ),
        400: example_error("No matches for ilab::train-samples-sc+cpu=10"),
        422: example_response(
            response={
                "detail": [
                    {
                        "message": "More than one metric (2) probably means you should add filters",
                        "names": {"dev": ["sdb", "sdb3"]},
                        "periods": [],
                    }
                ]
            }
        ),
    },
)
async def metric_summary(
    run: str,
    metric: str,
    name: Annotated[
        Optional[list[str]],
        Query(
            description="List of name[=key] to match",
            examples=["cpu=10", "cpu=10,cpu=110"],
        ),
    ] = None,
    period: Annotated[
        Optional[list[str]],
        Query(
            description="List of periods to match",
            examples=["<id>", "<id1>,<id2>"],
        ),
    ] = None,
):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metrics_summary(run, metric, names=name, periods=period)


@router.post(
    "/api/v1/ilab/runs/multigraph",
    summary="Returns overlaid Plotly graph objects",
    description="Returns metric data in a form usable by the Plot React component.",
    responses={
        200: example_response(
            response={
                "iostat::operations-merged-sec": [
                    {
                        "x": [
                            "2024-09-05 22:01:52+00:00",
                            "2024-09-05 21:56:37+00:00",
                            "2024-09-05 21:56:52+00:00",
                        ],
                        "y": [0.0, 0.0, 0.33],
                        "name": "Metric iostat::operations-merged-sec cmd=read,dev=sdb",
                        "type": "scatter",
                        "mode": "markers",
                        "orientation": "h",
                        "labels": {"x": "sample timestamp", "y": "samples / second"},
                    }
                ]
            }
        ),
        400: example_error("No matches for ilab::train-samples-sec"),
        422: example_response(
            response={
                "detail": [
                    {
                        "message": "More than one metric (2) probably means you should add filters",
                        "names": {"dev": ["sdb", "sdb3"]},
                        "periods": [],
                    }
                ]
            }
        ),
    },
)
async def metric_graph_body(graphs: GraphList):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metrics_graph(graphs)


@router.get(
    "/api/v1/ilab/runs/{run}/graph/{metric}",
    summary="Returns a single Plotly graph object for a run",
    description="Returns metric data in a form usable by the Plot React component.",
    responses={
        200: example_response(
            response={
                "iostat::operations-merged-sec": [
                    {
                        "x": [
                            "2024-09-05 22:01:52+00:00",
                            "2024-09-05 21:56:37+00:00",
                            "2024-09-05 21:56:52+00:00",
                        ],
                        "y": [0.0, 0.0, 0.33],
                        "name": "Metric iostat::operations-merged-sec cmd=read,dev=sdb",
                        "type": "scatter",
                        "mode": "markers",
                        "orientation": "h",
                        "labels": {"x": "sample timestamp", "y": "samples / second"},
                    }
                ]
            }
        ),
        400: example_error("No matches for ilab::train-samples-sec"),
        422: example_response(
            response={
                "detail": [
                    {
                        "message": "More than one metric (2) probably means you should add filters",
                        "names": {"dev": ["sdb", "sdb3"]},
                        "periods": [],
                    }
                ]
            }
        ),
    },
)
async def metric_graph_param(
    run: str,
    metric: str,
    aggregate: Annotated[
        bool, Query(description="Allow aggregation of metrics")
    ] = False,
    name: Annotated[
        Optional[list[str]],
        Query(
            description="List of name[=key] to match",
            examples=["cpu=10", "cpu=10,cpu=110"],
        ),
    ] = None,
    period: Annotated[
        Optional[list[str]],
        Query(
            description="List of periods to match",
            examples=["<id>", "<id1>,<id2>"],
        ),
    ] = None,
    title: Annotated[Optional[str], Query(description="Title for graph")] = None,
):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_metrics_graph(
        GraphList(
            run=run,
            name=metric,
            graphs=[
                Graph(
                    metric=metric,
                    aggregate=aggregate,
                    names=name,
                    periods=period,
                    title=title,
                )
            ],
        )
    )


@router.get(
    "/api/v1/ilab/info",
    summary="Returns info about the Crucible OpenSearch instance",
    description="Returns info about the Crucible OpenSearch instance",
    responses={
        200: example_response(
            {
                "name": "node.example.com",
                "cluster_name": "opensearch",
                "cluster_uuid": "YYaHMEjMT9G8z31-R7tJDA",
                "version": {
                    "distribution": "opensearch",
                    "number": "2.15.0",
                    "build_type": "rpm",
                    "build_hash": "61dbcd0795c9bfe9b81e5762175414bc38bbcadf",
                    "build_date": "2024-06-20T03:27:31.591886152Z",
                    "build_snapshot": False,
                    "lucene_version": "9.10.0",
                    "minimum_wire_compatibility_version": "7.10.0",
                    "minimum_index_compatibility_version": "7.0.0",
                },
            }
        ),
    },
)
async def info():
    crucible = CrucibleService(CONFIGPATH)
    return crucible.info


@router.get(
    "/api/v1/ilab/{index}/fields",
    summary="Returns a list of Crucible index fields",
    description="Returns a list of Crucible index fields.",
    responses={
        200: example_response(
            {
                "cdm": {"doctype": "keyword", "ver": "keyword"},
                "run": {
                    "begin": "date",
                    "benchmark": "keyword",
                    "desc": "text",
                    "email": "keyword",
                    "end": "date",
                    "harness": "keyword",
                    "host": "keyword",
                    "id": "keyword",
                    "name": "keyword",
                    "source": "keyword",
                    "tags": "text",
                },
            }
        ),
        400: example_error("Index name 'foo' doesn't exist"),
    },
)
async def fields(index: str):
    crucible = CrucibleService(CONFIGPATH)
    return crucible.get_fields(index=index)
