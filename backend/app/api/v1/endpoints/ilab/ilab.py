"""Access RHEL AI InstructLab performance data through Crucible

This defines an API to expose and filter performance data from InstructLab
CPT runs via a persistent Crucuble controller instance as defined in the
configuration path "ilab.crucible".
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Query

from app.services.crucible_svc import CrucibleService, GraphList, Metric

router = APIRouter()


CONFIGPATH = "ilab.crucible"


def example_response(response) -> dict[str, Any]:
    return {"content": {"application/json": {"example": response}}}


def example_error(message: str) -> dict[str, Any]:
    return example_response({"message": message})


async def crucible_svc():
    crucible = None
    try:
        crucible = CrucibleService(CONFIGPATH)
        yield crucible
    finally:
        if crucible:
            await crucible.close()


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
async def run_filters(crucible: Annotated[CrucibleService, Depends(crucible_svc)]):
    return await crucible.get_run_filters()


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
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
    all: Annotated[
        bool,
        Query(description="Don't apply default date range", examples=["all=true"]),
    ] = False,
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
    if not all and start_date is None and end_date is None:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)
        end = now
    else:
        start = start_date
        end = end_date
    return await crucible.get_runs(
        start=start, end=end, filter=filter, sort=sort, size=size, offset=offset
    )


@router.get(
    "/api/v1/ilab/runs/{run}/tags",
    summary="Returns the Crucible tags for a run",
    description="Returns tags for a specified Run ID.",
    responses={
        200: example_response({"topology": "none"}),
        400: example_error("Parameter error"),
    },
)
async def tags(crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str):
    return await crucible.get_tags(run)


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
async def params(crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str):
    return await crucible.get_params(run)


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
async def iterations(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str
) -> list[dict[str, Any]]:
    return await crucible.get_iterations(run)


@router.get(
    "/api/v1/ilab/runs/{run}/samples",
    summary="Returns a list of InstructLab run samples",
    description="Returns a list of samples for a specified Run ID.",
    responses={
        200: example_response(
            [
                {
                    "id": "6BBE6872-7139-11EF-BFAA-8569A9399D61",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                    "iteration": 5,
                    "primary_metric": "ilab::sdg-samples-sec",
                },
                {
                    "id": "6BACDFA8-7139-11EF-9F33-8185DD5B4869",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                    "iteration": 2,
                    "primary_metric": "ilab::sdg-samples-sec",
                },
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def run_samples(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str
) -> list[dict[str, Any]]:
    return await crucible.get_samples(run)


@router.get(
    "/api/v1/ilab/runs/{run}/periods",
    summary="Returns a list of InstructLab run periods",
    description="Returns a list of periods for a specified Run ID.",
    responses={
        200: example_response(
            [
                {
                    "begin": "2024-10-29 14:30:56.723000+00:00",
                    "end": "2024-10-29 14:35:18.939000+00:00",
                    "id": "DDBF3584-9603-11EF-8B3C-BAA807DC31B7",
                    "name": "measurement",
                    "iteration": 1,
                    "sample": "1",
                    "is_primary": True,
                    "primary_metric": "ilab::actual-train-seconds",
                    "status": "pass",
                },
                {
                    "begin": "1970-01-01 00:00:00+00:00",
                    "end": "1970-01-01 00:00:00+00:00",
                    "id": "DDB7FC92-9603-11EF-8FD6-97CFCD234564",
                    "name": "phase1",
                    "iteration": 1,
                    "sample": "1",
                    "is_primary": False,
                    "status": "pass",
                },
                {
                    "begin": "1970-01-01 00:00:00+00:00",
                    "end": "1970-01-01 00:00:00+00:00",
                    "id": "DDBBB5B2-9603-11EF-A19F-824975057E5B",
                    "name": "phase2",
                    "iteration": 1,
                    "sample": "1",
                    "is_primary": False,
                    "status": "pass",
                },
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def run_periods(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str
) -> list[dict[str, Any]]:
    return await crucible.get_periods(run)


@router.get(
    "/api/v1/ilab/iterations/{iteration}/samples",
    summary="Returns a list of InstructLab iteration samples",
    description="Returns a list of iterations for a specified iteration ID.",
    responses={
        200: example_response(
            [
                {
                    "id": "DDB759EA-9603-11EF-A714-9033EEFCCE93",
                    "num": "1",
                    "path": None,
                    "status": "pass",
                    "iteration": 1,
                    "primary_metric": "ilab::actual-train-seconds",
                    "primary_period": "measurement",
                }
            ]
        ),
        400: example_error("Parameter error"),
    },
)
async def iteration_samples(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], iteration: str
) -> list[dict[str, Any]]:
    return await crucible.get_samples(iteration=iteration)


@router.get(
    "/api/v1/ilab/runs/{run}/metrics",
    summary="Describe the metrics collected for a run",
    description="Returns metric labels along with breakout names and values.",
    responses={
        200: example_response(
            {
                "sar-net::packets-sec": {
                    "periods": [],
                    "breakouts": {
                        "benchmark-name": ["none"],
                        "benchmark-role": ["none"],
                        "csid": ["remotehosts-1-sysstat-1"],
                        "cstype": ["profiler"],
                        "dev": ["lo", "eno8303", "eno12399", "eno12409"],
                        "direction": ["rx", "tx"],
                        "endpoint-label": ["remotehosts-1"],
                        "engine-id": ["remotehosts-1-sysstat-1"],
                        "engine-role": ["profiler"],
                        "engine-type": ["profiler"],
                        "hosted-by": ["x.example.com"],
                        "hostname": ["x.example.com"],
                        "hypervisor-host": ["none"],
                        "osruntime": ["podman"],
                        "tool-name": ["sysstat"],
                        "type": ["virtual", "physical"],
                        "userenv": ["rhel-ai"],
                    },
                },
            },
        ),
        400: example_error("Parameter error"),
    },
)
async def metrics(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], run: str
):
    return await crucible.get_metrics_list(run)


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
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
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
) -> dict[str, Any]:
    return await crucible.get_metric_breakouts(run, metric, names=name, periods=period)


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
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
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
) -> list[dict[str, Any]]:
    return await crucible.get_metrics_data(
        run, metric, names=name, periods=period, aggregate=aggregate
    )


@router.post(
    "/api/v1/ilab/runs/multisummary",
    summary="Returns metric data summaries",
    description="Returns a statistical summary of metric data",
    responses={
        200: example_response(
            [
                {
                    "count": 1625,
                    "min": 0.0,
                    "max": 375.4,
                    "avg": 2.364492307692308,
                    "sum": 3842.3,
                    "sum_of_squares": 773029.4976,
                    "variance": 470.11963618840235,
                    "variance_population": 470.11963618840235,
                    "variance_sampling": 470.4091187230011,
                    "std_deviation": 21.68224241605103,
                    "std_deviation_population": 21.68224241605103,
                    "std_deviation_sampling": 21.68891695597088,
                    "std_deviation_bounds": {
                        "upper": 45.72897713979437,
                        "lower": -40.99999252440975,
                        "upper_population": 45.72897713979437,
                        "lower_population": -40.99999252440975,
                        "upper_sampling": 45.742326219634066,
                        "lower_sampling": -41.01334160424945,
                    },
                    "aggregate": True,
                    "metric": "iostat::operations-merged-sec",
                    "names": None,
                    "periods": None,
                    "run": "26ad48c1-fc9c-404d-bccf-d19755ca8a39",
                    "title": "iostat::operations-merged-sec {run 2}",
                }
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
async def metric_summary_body(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
    summaries: list[Metric],
) -> list[dict[str, Any]]:
    return await crucible.get_metrics_summary(summaries)


@router.get(
    "/api/v1/ilab/runs/{run}/summary/{metric}",
    summary="Returns metric data collected for a run",
    description="Returns data collected for a specified Run ID metric.",
    responses={
        200: example_response(
            {
                "count": 1625,
                "min": 0.0,
                "max": 375.4,
                "avg": 2.364492307692308,
                "sum": 3842.3,
                "sum_of_squares": 773029.4976,
                "variance": 470.11963618840235,
                "variance_population": 470.11963618840235,
                "variance_sampling": 470.4091187230011,
                "std_deviation": 21.68224241605103,
                "std_deviation_population": 21.68224241605103,
                "std_deviation_sampling": 21.68891695597088,
                "std_deviation_bounds": {
                    "upper": 45.72897713979437,
                    "lower": -40.99999252440975,
                    "upper_population": 45.72897713979437,
                    "lower_population": -40.99999252440975,
                    "upper_sampling": 45.742326219634066,
                    "lower_sampling": -41.01334160424945,
                },
                "aggregate": True,
                "metric": "iostat::operations-merged-sec",
                "names": None,
                "periods": None,
                "run": "26ad48c1-fc9c-404d-bccf-d19755ca8a39",
                "title": "iostat::operations-merged-sec {run 2}",
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
async def metric_summary_param(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
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
) -> dict[str, Any]:
    result = await crucible.get_metrics_summary(
        [
            Metric(
                run=run, metric=metric, aggregate=aggregate, names=name, periods=period
            )
        ]
    )
    return result[0] if isinstance(result, list) and len(result) == 1 else result


@router.post(
    "/api/v1/ilab/runs/multigraph",
    summary="Returns overlaid Plotly graph objects",
    description="Returns metric data in a form usable by the Plot React component.",
    responses={
        200: example_response(
            response={
                "data": [
                    {
                        "x": [
                            "2024-09-05 21:50:07+00:00",
                            "2024-09-05 21:56:37+00:00",
                            "2024-09-05 21:56:37.001000+00:00",
                            "2024-09-05 21:56:52+00:00",
                            "2024-09-05 21:56:52.001000+00:00",
                            "2024-09-05 22:01:52+00:00",
                        ],
                        "y": [0.0, 0.0, 0.33, 0.33, 0.0, 0.0],
                        "name": "iostat::operations-merged-sec [cmd=read,dev=sdb]",
                        "type": "scatter",
                        "mode": "line",
                        "marker": {"color": "black"},
                        "labels": {"x": "sample timestamp", "y": "samples / second"},
                        "yaxis": "y",
                    },
                    {
                        "x": [
                            "2024-09-05 21:50:07+00:00",
                            "2024-09-05 21:56:37+00:00",
                            "2024-09-05 21:56:37.001000+00:00",
                            "2024-09-05 21:56:52+00:00",
                            "2024-09-05 21:56:52.001000+00:00",
                            "2024-09-05 22:01:52+00:00",
                        ],
                        "y": [0.0, 0.0, 0.33, 0.33, 0.0, 0.0],
                        "name": "iostat::operations-merged-sec [dev=sdb,cmd=read]",
                        "type": "scatter",
                        "mode": "line",
                        "marker": {"color": "purple"},
                        "labels": {"x": "sample timestamp", "y": "samples / second"},
                        "yaxis": "y",
                    },
                ],
                "layout": {
                    "width": "1500",
                    "yaxis": {
                        "title": "iostat::operations-merged-sec",
                        "color": "black",
                    },
                },
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
async def metric_graph_body(
    crucible: Annotated[CrucibleService, Depends(crucible_svc)], graphs: GraphList
):
    return await crucible.get_metrics_graph(graphs)


@router.get(
    "/api/v1/ilab/runs/{run}/graph/{metric}",
    summary="Returns a single Plotly graph object for a run",
    description="Returns metric data in a form usable by the Plot React component.",
    responses={
        200: example_response(
            response={
                "data": [
                    {
                        "x": [
                            "2024-09-12 16:49:01+00:00",
                            "2024-09-12 18:04:31+00:00",
                            "2024-09-12 18:04:31.001000+00:00",
                            "2024-09-12 18:04:46+00:00",
                            "2024-09-12 18:04:46.001000+00:00",
                            "2024-09-12 18:53:16+00:00",
                        ],
                        "y": [0.0, 0.0, 1.4, 1.4, 0.0, 0.0],
                        "name": "iostat::operations-merged-sec [cmd=read,dev=sda]",
                        "type": "scatter",
                        "mode": "line",
                        "marker": {"color": "black"},
                        "labels": {
                            "x": "sample timestamp",
                            "y": "samples / second",
                        },
                        "yaxis": "y",
                    }
                ],
                "layout": {
                    "width": "1500",
                    "yaxis": {
                        "title": "iostat::operations-merged-sec",
                        "color": "black",
                    },
                },
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
    crucible: Annotated[CrucibleService, Depends(crucible_svc)],
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
    return await crucible.get_metrics_graph(
        GraphList(
            name=metric,
            graphs=[
                Metric(
                    run=run,
                    metric=metric,
                    aggregate=aggregate,
                    names=name,
                    periods=period,
                    title=title,
                )
            ],
        )
    )
