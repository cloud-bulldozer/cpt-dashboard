Crucible divides data across a set of OpenSearch (or ElasticSearch) indices,
each with a specific document mapping. CDM index names include a "root" name
(like "run") with a versioned prefix, like "cdmv7dev-run".

Crucible timestamps are integers in "millisecond-from-the-epoch" format.

The Crucible CDM hierarchy is roughly:

- RUN (an instrumented benchmark run)
  - TAG (metadata)
  - ITERATION (a benchmark interval)
    - PARAM (execution parameters)
    - SAMPLE
      - PERIOD (time range where data is recorded)
        - METRIC_DESC (description of a specific recorded metric)
          - METRIC_DATA (a specific recorded data point)

OpenSearch doesn't support the concept of a SQL "join", but many of the indices
contain documents that could be considered a static "join" with parent documents
for convenience. For example, each `iteration` document contains a copy of the
parent `run` document, while the `period` document contains copies of its parent
`sample`, `iteration`, and `run` documents. This means, for example, that it's
possible to make a single query returning all `period` documents for specific
iteration number of a specific run.

<dl>
<dt>RUN</dt><dd>this contains the basic information about a performance run, including a
    generated UUID, begin and end timestamps, a benchmark name, a user name and
    email, the (host/directory) "source" of the indexed data (which is usable on
    the controler's local file system), plus host and test harness names.</dd>
<dt>TAG</dt><dd>this contains information about a general purpose "tag" to associate some
    arbitrary context with a run, for example software versions, hardware, or
    other metadata. This can be considered a SQL JOIN with the run document,
    adding a tag UUID, name, and value.</dd>
<dt>ITERATION</dt><dd>this contains basic information about a performance run iteration,
    including the iteration UUID, number, the primary (benchmark) metric associated
    with the iteration, plus the primary "period" of the iteration, and the
    iteration status.</dd>
<dt>PARAM</dt><dd>this defines a key/value pair specifying behavior of the benchmark
    script for an iteration. Parameters are iteration-specific, but parameters that
    don't vary between iterations are often represented as run parameters.</dd>
<dt>SAMPLE</dt><dd>this contains basic information about a sample of an iteration,
    including a sample UUID and sample number, along with a "path" for sample data
    and a sample status.</dd>
<dt>PERIOD</dt><dd>this contains basic information about a period during which data is
    collected within a sample, including the period UUID, name, and begin and end
    timestamps. A set of periods can be "linked" through a "prev_id" field.</dd>
<dt>METRIC_DESC</dt><dd>this contains descriptive data about a specific series
    of metric values within a specific period of a run, including the metric UUID,
    the metric "class", type, and source, along with a set of "names" (key/value
    pairs) defining specific sample attributes within a source and type. For
    example source:mpstat, type:Busy-CPU (commonly represented as `mpstat::Busy-CPU`)
    samples are recorded by processor mode for a specific thread, core, package,
    etc.</dd>
<dt>METRIC_DATA</dt><dd>this describes a specific data point, sampled over a specified
    duration with a fixed begin and end timestamp, plus a floating point value.
    Each is tied to a specific metric_desc UUID value. Depending on the varied
    semantics of metric_desc `nam`e attributes, it's often valid to aggregate these
    values by source and type, for example to get the total CPU load. You can
    also "break out" the day by `name` attribute values, for example to show
    the CPU load for each CPU core or processor mode.</dd>
</dl>

The `crucible_svc` allows CPT project APIs to access a Crucible CDM backing
store to find information about runs, tags, params, iterations, samples,
periods, plus various ways to expose and aggregate metric data both for
primary benchmarks and non-periodic tools.

The Crucible service supports a range of CDM (Common Data Model) versions. An
OpenSearch instance may support either CDMv7, CDMv8, or CDMv9. Version 9 adds
support for a shared OpenSearch instance with a design that intends to support
mixing several versions; so that, in the future, Crucible would support a single
server with both CDMv9 and CDMv10 indices, interleaving results from all indices
within a specified date range.

Note that while the Crucible service currently supports both CDMv7 and CDMv8, CDMv8
will be automatically selected if CDMv8 indices exist; the service will use only
one set of indices (either CDMv7 or CDMv8) after initialization.

The `get_runs` API is the primary entry point, returning an object that
supports filtering, sorting, and pagination of the Crucible run data decorated
with useful iteration, tag, and parameter data.

The metrics data APIs (data, breakouts, summary, and graph) allow
filtering by the metric `name` attribute values. This allows "drilling down"
through the non-periodic "tool data". For example, IO data is per-disk, CPU
information is broken down by core and package. You can aggregate
all global data (e.g., total system CPU), or break out more specific
data by `name` attribute values to select by CPU, mode (usr, sys, irq), etc.

For example, to return `Busy-CPU` ("type") graph data from the `mpstat`
("source") tool for system mode on one core, you might query:

```
/api/v1/ilab/runs/<id>/graph/mpstat::Busy-CPU?name=core=12,package=1,num=77,type=sys
```

If you make a `graph`, `data`, or `summary` query that doesn't translate
to a unique metric descriptor ID, and don't select aggregation, you'll get a
diagnostic message identifying possible additional filters. For example,
you might see a message like this:

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
allow displaying metric details. The `get_metrics` API will show all
recorded metrics, along with the (breakout) `name` attribute values available
in those metrics. Metrics that show "names" with more than one value will need
to be filtered (or aggregated) to produce meaningful summaries or graphs.

You can aggregate metrics across `name` attribute values using the
`?aggregate` query parameter. For example,
`GET /api/v1/ilab/runs/<id>/graph/mpstat::Busy-CPU?aggregate`
will aggregate all CPU busy data for the selected run.

This capability can be used to build an interactive exploratory UI to allow
displaying metric details. The `get_metrics` API will show all recorded
metrics, along with the names and values available for breakout. Metrics that
show "names" with more than one value will need to be filtered (or aggregated)
to produce meaningful summaries or graphs.

Normally you'll want to display data based on sample periods, for example the
primary period of an iteration, using `?period=<period-id>`. This will
implicitly constrain the metric data based on the period ID associated with
the `metric_desc` document and the begin/end timestamps of the selected
period(s). Normally, a benchmark will define separate iterations when each
is run with different parameter value(s), and the default graph labeling will
look for a set of distinct parameters not used by other iterations: for
example, `mpstat::Busy-CPU (batch-size=16)`. (You can also override the label
for each graph if desired.)

The `get_breakouts` API can be used to explore the namespace recorded for that
metric in the specified run. For example,

```
GET /api/v1/ilab/runs/<id>/breakouts/sar-net::packets-sec?name=direction=rx
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

The `get_filters` API reports all the tag and param filter tags and
values for the runs. These can be used for the `filters` query parameter
on `get_runs` to restrict the set of runs reported; for example,
`/api/v1/ilab/runs?filter=param:workflow=sdg` shows only runs with the param
arg `workflow` set to the value `sdg`. You can search for a subset of the
string value using the operator "~" instead of "=". For example,
`?filter=param:user~user` will match `user` values of "A user" or "The user".
