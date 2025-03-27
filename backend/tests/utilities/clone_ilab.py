"""Clone a live Crucible CDM v7 Opensearch instance

This is used to bootstrap a functional test environment by starting with a live
CDM database.

E.g.:
    python3 tests/utilities/clone_ilab.py \
        http://n42-h01-b01-mx750c.rdu3.labs.perfscale.redhat.com:9200 \
        http://localhost:9200 \
        --ids tests/utilities/anointed.txt

TODO: Update to handle CDM v8
"""

import argparse
from pathlib import Path
import sys
import time
from typing import Any, Iterator, Optional
from elasticsearch import Elasticsearch

indices = (
    "run",
    "iteration",
    "sample",
    "period",
    "tag",
    "param",
    "metric_desc",
)


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


def clone(source_server: str, target_server: str, ids: list[str]):
    target = Elasticsearch(target_server)
    source = Elasticsearch(source_server)

    if ids:
        query = {"query": {"bool": {"filter": {"terms": {"run.id": ids}}}}}
    else:
        query = None
    for i in indices:
        start = time.time()
        name = index(i)
        print(f"Migrating {name}")
        r = target.indices.delete(name, ignore_unavailable=True)
        if not r["acknowledged"]:
            print(f"delete {name} failed: {r}", file=sys.stderr)
            continue
        if target.indices.exists_template(name):
            r = target.indices.delete_template(name)
            if not r.get("acknowledged"):
                print(f"Problem deleting template {name}: {r}", file=sys.stderr)
                continue
        response = source.indices.get_template(name=name)
        template = response.get(name)
        if not template:
            print(f"Problem getting template {name}: {response}")
            continue
        r = target.indices.put_template(name, body=template)
        if not r.get("acknowledged"):
            print(f"Problem deleting template {name}: {r}", file=sys.stderr)
            continue
        body = {
            "source": {"remote": {"host": source_server}, "index": name},
            "dest": {"index": name},
            "size": 250000
        }
        if query:
            body["source"].update(query)
        r = target.reindex(
            body=body,
            timeout="5m",
            request_timeout=1000.0,
        )
        if r.get("failures"):
            print(f"Problem reindexing (cloning) {name}: {r}", file=sys.stderr)
            continue
        print(
            f"Done migrating {name} ({r.get('total')} documents): {time.time()-start:.3f} seconds"
        )

    # We have to handle metric_data differently, because those documents don't
    # have run subdocuments. Instead, we need to collect all of the metric_desc
    # IDs for the runs we've transferred (a query against the target), and then
    # use that list to transfer all associated metric_desc documents.
    #
    # We'll just get all metric_desc documents -- if we're cloning a set, the
    # target has only the selected runs.
    idx = index("metric_desc")
    name = index("metric_data")
    r = target.search(size=250000, index=idx)
    metrics = [h["metric_desc"]["id"] for h in hits(r)]
    if len(metrics) == 0:
        print(f"funky: {r}")
    print(f"Migrating {name} for {len(metrics)} metrics")
    start = time.time()
    r = target.reindex(
        body={
            "source": {
                "query": {"bool": {"filter": {"terms": {"metric_desc.id": metrics}}}},
                "remote": {"host": source_server},
                "index": name,
            },
            "dest": {"index": name},
            "size": 250000
        },
        timeout="5m",
        request_timeout=1000.0,
    )
    if r.get("failures"):
        print(f"Problem reindexing (cloning) {name}: {r}", file=sys.stderr)
    print(
        f"Done migrating {name} ({r.get('total')} documents): {time.time()-start:.3f} seconds"
    )


parser = argparse.ArgumentParser("clone")
parser.add_argument("source", help="Crucible Opensearch server address")
parser.add_argument("target", help="Functional test Opensearch server address")
parser.add_argument(
    "-i",
    "--ids",
    dest="ids",
    help="Read a list of run IDs from the named file",
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
print(f"SOURCE: {args.source}")
print(f"TARGET: {args.target}")

try:
    ids = []
    if args.ids:
        try:
            ids = Path(args.ids).read_text().splitlines()
        except FileNotFoundError:
            print(f"File {args.ids} not found", file=sys.stderr)
            sys.exit(1)
        print(f"Annointed runs: {ids}")
    clone(args.source, args.target, ids)
    sys.exit(0)
except Exception as exc:
    print(f"Something smells odd: {str(exc)!r}")
    sys.exit(1)
