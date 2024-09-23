The `crucible_svc` allows CPT project APIs to access a Crucible CDM backing
store to find information about runs, tags, params, iterations, samples,
periods, plus various ways to expose and aggregate metric data both for
primary benchmarks and non-periodic tools.

The `get_runs` API is the primary entry point, returning an object that
supports filtering, sorting, and pagination of the Crucible run data decorated
with useful iteration, tag, and parameter data.

The metrics data APIs (data, breakouts, summary, and graph) now allow
filtering by the metric "name" data. This allows "drilling down" through
the non-periodic "tool data". For example, IO data is per-disk, CPU
information is broken down by core and package. You can now aggregate
all global data (e.g., total system CPU), or filter by breakout names to
select by CPU, mode (usr, sys, irq), etc.

For example, to return `mpstat` `Busy-CPU` graph data for one core, you
might query:

```
/api/v1/ilab/runs/f542a50c-55df-4ead-92d1-8c55367f2e79/graph/mpstat::Busy-CPU?name=core=12,package=1,num=77,type=guest
```

If you make a `graph`, `data`, or `summary` query that doesn't translate
to a unique metric, and don't allow aggregation, you'll get a diagnostic
message identifying possible additional filters. For example, with
`type=guest` removed, that same query will show the available values for
the `type` name:

```
{
  "detail": [
    {
      "message": "More than one metric (5) probably means you should add filters",
      "names": {
        "type": [
          "guest",
          "irq",
          "soft",
          "sys",
          "usr"
        ]
      },
      "periods": []
    }
  ]
}
```

This capability can be used to build an interactive exploratory UI to
allow displaying breakout details. The `get_metrics` API will show all
recorded metrics, along with information the names and values used in
those. Metrics that show "names" with more than one value will need to be
filtered to produce meaningful summaries or graphs. The `get_breakdowns` API
can be used to explore the namespace recorded for that metric in the specified
run. For example,

```
GET /api/v1/ilab/runs/<id>/breakdowns/sar-net::packets-sec?name=direction=rx
{
  "label": "sar-net::packets-sec",
  "source": "sar-net",
  "type": "packets-sec",
  "class": [],
  "names": {
    "dev": [
      "lo",
      "eno12409",
      "eno12399"
    ],
    "type": [
      "physical",
      "virtual"
    ]
  }
}
```

Metric data access (including graphing) is now sensitive to the Crucible
"period". The UI iterates through all periods for the selected run,
requesting the primary metric and a selected secondary non-periodic
metric for each period. The labeling for the graph is based on finding
"param" values unique for each period's iteration.

The `get_filters` API reports all the tag and param filter tags and
values for the runs. These can be used for the `filters` query parameter
on `get_runs` to restrict the set of runs reported; for example,
`/api/v1/ilab/runs?filter=param:workflow=sdg` shows only runs with the param
arg `workflow` set to the value `sdg`.
