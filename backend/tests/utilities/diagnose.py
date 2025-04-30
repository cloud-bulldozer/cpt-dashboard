"""Tool to analyze CDM data to help identify "broken" runs.

Traverse the CDM hierarchy (run to iteration to sample to period to metric
descriptors and data) to identify inconsistencies and incomplete data.

The purpose is to help identify "anointed" sample runs to migrate into the
captive Opensearch snapshot for functional testing; but this can be used to
validate any CDMv7 Opensearch instance.
"""

from collections import defaultdict
from dataclasses import dataclass, field
import datetime
import sys
from threading import Thread
import time
from typing import Any, Iterator, Optional, Union
from elasticsearch import Elasticsearch
import argparse


@dataclass
class Info:
    """Accumulate summary information about a run"""
    id: str
    good: bool = True
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    begin: int = 0
    end: int = 0
    benchmark: str = ""
    tags: dict[str, str] = field(default_factory=lambda: defaultdict(str))
    iterations: int = 0
    params: dict[int, dict[str, str]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(str))
    )
    samples: int = 0
    periods: int = 0
    primary: set[str] = field(default_factory=set)
    metrics: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    points: int = 0


class Verify:
    """Encapsulate -v status messages."""

    def __init__(self, verify: Union[bool, int]):
        """Initialize the object.

        Args:
            verify: True to write status messages.
        """
        if isinstance(verify, int):
            self.verify = verify
        else:
            self.verify = 1 if verify else 0

    def __bool__(self) -> bool:
        """Report whether verification is enabled.

        Returns:
            True if verification is enabled.
        """
        return bool(self.verify)

    def status(self, message: str, level: int = 1):
        """Write a message if verification is enabled.

        Args:
            message: status string
        """
        if self.verify >= level:
            ts = datetime.datetime.now().astimezone()
            print(f"({ts:%H:%M:%S}) {message}", file=sys.stderr)


class Watch:
    """Encapsulate a periodic status update.

    The active message can be updated at will; a background thread will
    periodically print the most recent status.
    """

    def __init__(self, interval: float):
        """Initialize the object.

        Args:
            interval: interval in seconds for status updates
        """
        self.start = time.time()
        self.interval = interval
        self.status = "starting"
        if interval:
            self.thread = Thread(target=self.watcher)
            self.thread.setDaemon(True)
            self.thread.start()

    def update(self, status: str):
        """Update status if appropriate.

        Update the message to be printed at the next interval, if progress
        reporting is enabled.

        Args:
            status: status string
        """
        self.status = status

    def watcher(self):
        """A worker thread to periodically write status messages."""

        while True:
            time.sleep(self.interval)
            now = time.time()
            delta = int(now - self.start)
            hours, remainder = divmod(delta, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(
                f"[{hours:02d}:{minutes:02d}:{seconds:02d}] {self.status}",
                file=sys.stderr,
            )


watcher: Optional[Watch] = None
verifier: Optional[Verify] = None


def index(root: str) -> str:
    return f"cdmv7dev-{root}"


def hits(
    payload: dict[str, Any], fields: Optional[list[str]] = None
) -> Iterator[dict[str, Any]]:
    """Helper to iterate through OpenSearch query matches

    Iteratively yields the "_source" of each hit. As a convenience, can
    yield a sub-object of "_source" ... for example, specifying the
    optional "fields" as ["metric_desc", "id"] will yield the equivalent of
    hit["_source"]["metric_desc"]["id"]

    Args:
        payload: OpenSearch reponse payload
        fields: Optional sub-fields of "_source"

    Returns:
        Yields each object from the "greatest hits" list
    """
    if "hits" not in payload:
        raise Exception(f"Attempt to iterate hits for {payload}")
    hits = payload.get("hits", {}).get("hits", [])
    for h in hits:
        source = h["_source"]
        if fields:
            for f in fields:
                source = source[f]
        yield source


def diagnose(cdm: Elasticsearch, args: argparse.Namespace):
    """Traverse a CDM database and accumulate information.

    We record an Info object for each run, including information about broken
    and inconsistent documents, and report the outcome.

    The analysis can take a while -- we use the Watcher class to show periodic
    progress messages if requested.
    """
    start = time.time()
    runs = {}
    watcher.update("finding runs")
    rq = cdm.search(index=index("run"), sort=["run.begin:asc"], size=10000)
    for r in hits(rq, ["run"]):
        info = Info(r["id"], benchmark=r["benchmark"])
        runs[info.id] = info
        info.begin = r.get("begin", 0)
        info.end = r.get("end", 0)
        if not info.begin or not info.end:
            info.errors["missing/bad run timestamps"] += 1
            info.good = False
        watcher.update(f"finding {info.id} tags")
        tq = cdm.search(
            index=index("tag"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        info.tags = {t["name"]: t["val"] for t in hits(tq, ["tag"])}
        watcher.update(f"finding {info.id} iterations")
        iq = cdm.search(
            index=index("iteration"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        info.iterations = len(iq["hits"]["hits"])
        info.primary.update((i["primary-metric"] for i in hits(iq, ["iteration"])))
        watcher.update(f"finding {info.id} params")
        pq = cdm.search(
            index=index("param"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        for p in hits(pq):
            i = p["iteration"]["num"]
            param = p["param"]
            info.params[i][param["arg"]] = param["val"]
        watcher.update(f"finding {info.id} samples")
        sq = cdm.search(
            index=index("sample"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        info.samples = len(sq["hits"]["hits"])
        watcher.update(f"finding {info.id} periods")
        pq = cdm.search(
            index=index("period"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        info.periods = len(iq["hits"]["hits"])
        for p in hits(pq, ["period"]):
            b = p.get("begin")
            e = p.get("end")
            if not b or not e:
                info.errors[f"period {p['name']}: missing/bad timestamps"] += 1
                info.good = False
        watcher.update(f"finding {info.id} metrics")
        mq = cdm.search(
            index=index("metric_desc"),
            body={"query": {"bool": {"filter": {"term": {"run.id": info.id}}}}},
            size=10000,
        )
        metrics = {}
        for m in hits(mq, ["metric_desc"]):
            name = f"{m['source']}::{m['type']}"
            metrics[m["id"]] = name
            info.metrics[name] = 0
        watcher.update(f"finding {info.id} metric data")
        dq = cdm.search(
            index=index("metric_data"),
            body={
                "query": {
                    "bool": {
                        "filter": {"terms": {"metric_desc.id": list(metrics.keys())}}
                    }
                }
            },
            size=100000,
        )
        for d in hits(dq):
            id = d["metric_desc"]["id"]
            data = d["metric_data"]
            info.metrics[metrics[id]] += 1
            if not data.get("begin") or not data.get("end"):
                info.good = False
                info.errors[f"metric {metrics[id]} sample missing timestamp"] += 1
            if "duration" not in data:
                info.good = False
                info.errors[f"metric {metrics[id]} sample missing duration"] += 1
            if "value" not in data:
                info.good = False
                info.errors[f"metric {metrics[id]} sample missing value"] += 1

    watcher.update(f"generating report")
    baddies = 0
    marks = defaultdict(int)
    first = True
    for run in runs.values():
        if not run.good:
            baddies += 1
        if (run.good and args.bad) or (not run.good and args.good):
            continue
        marks[run.benchmark] += 1
        if args.id:
            print(run.id)
            continue
        t = datetime.datetime.fromtimestamp(
            int(run.begin) / 1000.0, tz=datetime.timezone.utc
        )
        if not args.detail:
            if first:
                first = False
                print(
                    f"{'Run ID':<36s} {'Benchmark':<10s} {'Start time':<16s} It Sa Pd Errors Primary"
                )
                print(
                    f"{'':-<36s} {'':-<10s} {'':-<16s} {'':-<2s} {'':-<2s} {'':-<2s} {'':-<6s} {'':-<20s}"
                )
            print(
                f"{run.id:36s} {run.benchmark:10s} {t:%Y-%m-%d %H:%M} "
                f"{run.iterations:>2d} {run.samples:>2d} {run.periods:>2d} "
                f"{sum(run.errors.values()) if run.errors else 0:>6d} "
                f"{','.join(sorted(run.primary))}"
            )
            continue
        print(f"Run {run.id} ({run.benchmark}@{t:%Y-%m-%d %H:%M})")
        print(f"  Tags: {','.join(f'{k}={v}' for k, v in run.tags.items())}")
        print(
            f"  {run.iterations} iterations: primary metrics {', '.join(sorted(run.primary))}"
        )
        if run.params:
            print("  Iteration params:")
            for i, p in run.params.items():
                for k, v in p.items():
                    print(f"    {i:>2d} {k}={v}")
        print(f"  {run.samples} samples")
        print(f"  {run.periods} periods")
        if run.metrics:
            print("  Metrics:")
            for m in sorted(run.metrics.keys()):
                print(f"    {m:>15s}: {run.metrics[m]:5d}")
        if not run.good:
            print("  Errors:")
            for e, i in run.errors.items():
                print(f"    ({i:>3d}) {e!r}")
    if args.summary or not args.id:
        print(f"{len(runs)} runs analyzed: {baddies} are busted")
        print("Benchmarks:")
        for b in sorted(marks.keys()):
            print(f"  {b:>10s}: {marks[b]:5d}")
        print(f"Analysis took {time.time() - start:03f} seconds")


parser = argparse.ArgumentParser("diagnose")
parser.add_argument("server", help="CDM v7 Opensearch server address")
parser.add_argument(
    "-b", "--bad-only", dest="bad", action="store_true", help="Only report bad runs"
)
parser.add_argument(
    "-g", "--good-only", dest="good", action="store_true", help="Only report good runs"
)
parser.add_argument(
    "-i",
    "--id-only",
    dest="id",
    action="store_true",
    help="Report just IDs (with good-only or bad-only)",
)
parser.add_argument(
    "-d", "--detail", dest="detail", action="store_true", help="Report detail on runs"
)
parser.add_argument(
    "-s",
    "--summary",
    dest="summary",
    action="store_true",
    help="Print summary statistics",
)
parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    action="count",
    default=0,
    help="Give progress feedback",
)
parser.add_argument("--version", action="version", version="%(prog)s 0.1")

args = parser.parse_args()

verifier = Verify(args.verbose)
watcher = Watch(60.0 / args.verbose if args.verbose else 0)

try:
    cdm = Elasticsearch(args.server)
    diagnose(cdm, args)
    sys.exit(0)
except Exception as exc:
    print(f"Something smells odd: {str(exc)!r}")
    sys.exit(1)
