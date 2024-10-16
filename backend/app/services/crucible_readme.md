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
for convenience. For example, each `iteration` document contains a copy of it's
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
    pairs) defining the metric breakout details that narrow down a specific source and
    type. For example source:mpstat, type:Busy-CPU data is broken down by package, cpu,
    core, and other breakouts which can be isolated or aggregated for data reporting.</dd>
<dt>METRIC_DATA</dt><dd>this describes a specific data point, sampled over a specified
    duration with a fixed begin and end timestamp, plus a floating point value.
    Each is tied to a specific metric_desc UUID value. Depending on the varied
    semantics of metric_desc breakouts, it's often valid to aggregate these
    across a set of relatead metric_desc IDs, based on source and type, for
    example to get aggregate CPU load across all modes, cores, or across all
    modes within a core. This service allows arbitrary aggregation within a
    given metric source and type, but by default will attempt to direct the
    caller to specifying a set of breakouts that result in a single metric_desc
    ID.</dd>
</dl>

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

For example, to return `Busy-CPU` ("type") graph data from the `mpstat`
("source") tool for system mode on one core, you might query:

```
/api/v1/ilab/runs/<id>/graph/mpstat::Busy-CPU?name=core=12,package=1,num=77,type=sys
```

If you make a `graph`, `data`, or `summary` query that doesn't translate
to a unique metric, and don't select aggregation, you'll get a diagnostic
message identifying possible additional filters. For example, with
`type=sys` removed, that same query will show the available values for
the `type` breakout name:

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
filtered to produce meaningful summaries or graphs.

You can instead aggregate metrics across breakouts using the `?aggregate`
query parameter, like `GET /api/v1/ilab/runs/<id>/graph/mpstat::Busy-CPU?aggregate`
which will aggregate all CPU busy data for the system.

Normally you'll want to display data based on sample periods, for example the
primary period of an iteration, using `?period=<period-id>`. This will
implicitly constrain the metric data based on the period ID associated with
the `metric_desc` document *and* the begin/end time period of the selected
periods. Normally, a benchmark will will separate iterations because each is
run with a different parameter value, and the default graph labeling will
look for a set of distinct parameters not used by other iterations: for
example, `mpstat::Busy-CPU (batch-size=16)`.

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
