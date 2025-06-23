#!/usr/bin/env python3
"""Clone a live Crucible CDM v8 Opensearch instance

This is used to bootstrap a functional test environment by starting with a live
CDM database.

E.g.:
    python3 tests/utilities/clone_ilab.py --clone \
        http://n42-h01-b01-mx750c.rdu3.labs.perfscale.redhat.com:9200 \
        http://localhost:9200 \
        --ids tests/utilities/anointed.txt

This process will take a while; you can use --watch <seconds> for a periodic
progress update, an --verify will announce the various steps it takes.

You can combine runs from multiple sources by running the utility multiple
times with --clone and different source URLs. Once you have the target
database ready, you can use --snapshot to create a new OpenSearch snapshot
inside the container.

Note that this utility doesn't manage the OpenSearch container; this gives
you more flexibility, and it's not intended to be run often. You can create
a local OpenSearch container for ILAB using

    COMPONENT=ilab \
    OPENSEARCH_YML=${PWD}/tests/utilities/clone_opensearch.yml \
        ../testing/opensearch.sh

The "clone_opensearch.yml" includes whitelisted remote reindex URLs: you
may need to edit this before using it to include your source OpenSearch
servers.

Once you've populated your database and created a snapshot, you can retrieve
the snapshot using something like the following command sequence:

    podman exec -it opensearch_ilab bash
        $ cd /var/tmp
        $ tar czf snapshot.tar.gz snapshot
    podman cp opensearch_ilab:/var/tmp/snapshot.tar.gz testing/ilab/
"""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import sys
from threading import Thread
import time
from typing import Any, Iterator, Optional, Union
from urllib.parse import urlparse

from elasticsearch import Elasticsearch

BIG = 262144


INDICES = (
    "run",
    "iteration",
    "sample",
    "period",
    "tag",
    "param",
    "metric_desc",
)


VERSION: str = "v8dev"


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
            ts = datetime.now().astimezone()
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


@dataclass
class Host:
    url: str
    username: Optional[str]
    password: Optional[str]


def parse_url(server: str) -> Host:
    url = urlparse(server)
    if url.port:
        port = url.port
    elif url.scheme == "https":
        port = 443
    else:
        port = 80
    host = f"{url.scheme}://{url.hostname}:{port}"
    return Host(host, url.username, url.password)


def open_opensearch(server: str) -> Elasticsearch:
    host = parse_url(server)
    verifier.status(
        f"HOST: {host.url}, AUTH: {host.username}, {host.password}", level=2
    )
    auth = (host.username, host.password) if host.username else None
    return Elasticsearch(
        host.url, http_auth=auth, verify_certs=False, ssl_show_warn=False
    )


def detect_versions(server: Elasticsearch):
    global VERSION
    indices = server.indices.get(
        "cdm*-run*", allow_no_indices=True, ignore_unavailable=True
    )
    versions = set()
    vpat = re.compile(r"cdm-?(?P<version>v\d+dev)-")
    for i in indices.keys():
        match = vpat.match(i)
        if match:
            try:
                versions.add(match.group("version"))
            except Exception as e:
                if args.verbose:
                    print(f"Skipping index {i}: {str(e)!r}")
    if args.verbose:
        print(f"Found CDM versions {versions}")
    if len(versions) > 1:
        raise Exception(
            "Sorry, but I'm not currently programmed to handle multiple source CDM versions!"
        )
    VERSION = next(iter(versions))
    print(f"Using version {VERSION}")


def index(root: str) -> str:
    if VERSION < "v9dev":
        return f"cdm{VERSION}-{root}"
    else:
        return f"cdm-{VERSION}-{root}@*"


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


def clone_index(source: Elasticsearch, target: Elasticsearch, index: str):
    response = source.indices.get_mapping(index=index)
    if VERSION < "v9dev" and len(response.keys()) > 1:
        raise Exception(
            f"Something's off: {VERSION} index {index} has more than one mapping"
        )
    for i, mapping in response.items():
        if not mapping or "mappings" not in mapping:
            print(f"Problem getting mapping {i}: {response}", file=sys.stderr)
            raise Exception("She canna take it, captain!")
        r = target.indices.delete(i, ignore_unavailable=True)
        if not r["acknowledged"]:
            print(f"delete {i} failed: {r}", file=sys.stderr)
            raise Exception("She canna take it, captain!")
        mapping["settings"] = {"index": {"max_result_window": BIG}}
        r = target.indices.create(
            index=i,
            body=mapping,
        )
        if not r.get("acknowledged"):
            print(f"Problem creating {i}: {r}", file=sys.stderr)
            raise Exception("She canna take it, captain!")


def clone(source: Elasticsearch, target: Elasticsearch, ids: list[str]):
    if ids:
        query = {"query": {"bool": {"filter": {"terms": {"run.run-uuid": ids}}}}}
    else:
        query = None
    for i in INDICES:
        watcher.update(f"cloning {i}")
        start = time.time()
        pattern = index(i)
        names = [pattern]

        # The reindex operation doesn't handle wildcarded indices so we need to
        # expand the wildcards for CDMv9 and transfer each timeseries index
        # name separately.
        if "*" in pattern:
            names = source.indices.get(index=pattern).keys()

        # The reindex operation is picky about URLs; it always assumes a port,
        # and defaults to 9200 if one is specified. That presents a problem for
        # the INTLAB OpenSearch service, where the default 443 TLS port becomes
        # 9200, which doesn't work. We need to construct the actual ful URL.
        #
        # TODO: I tried pulling out the credentials into the explicit username
        # and password first, and I suspect that's not necessary but don't feel
        # like reverting that (and possibly discovering that it was necessary);
        # but this might be worth experimenting later.
        host = parse_url(args.source)
        remote = {"host": host.url}
        if host.username:
            remote["username"] = host.username
            remote["password"] = host.password
        for name in names:
            if args.verbose:
                print(f"Cloning {name}")
            clone_index(source, target, name)
            body = {
                "source": {"remote": remote, "index": name},
                "dest": {"index": name},
            }
            if query:
                body["source"].update(query)
            r = target.reindex(
                body=body,
                timeout="5m",
                request_timeout=1000.0,
                wait_for_completion=True,
                refresh=True,
            )
            if r.get("failures"):
                print(f"Problem reindexing (cloning) {name}: {r}", file=sys.stderr)
                continue
            print(
                f"Done cloning {name} ({r.get('total')} documents): {time.time()-start:.3f} seconds"
            )

    # We handle metric_data differently, because the number of metric data
    # documents is usually beyond the capacity of a single OpenSearch
    # "_reindex" operation. To avoid overflow we're going to subdivide them
    # into batches based on metric_desc UUIDs.
    start = time.time()
    buckets = defaultdict(list)
    idx = index("metric_desc")
    r = target.search(size=BIG, index=idx)
    pattern = index("metric_data")
    names = [pattern]
    if "*" in pattern:
        names = source.indices.get(index=pattern).keys()

    if args.verbose:
        print(f"Metric data: found {len(r['hits']['hits'])} descriptors")
    for h in hits(r, ["metric_desc"]):
        buckets[f"{h['source']}::{h['type']}"].append(h["metric_desc-uuid"])
    id_field = "metric_desc.metric_desc-uuid"
    total_ids = 0
    total_data = 0
    host = parse_url(args.source)
    remote = {"host": host.url}
    if host.username:
        remote["username"] = host.username
        remote["password"] = host.password
    for name in names:
        print(f"Cloning {name} for {len(buckets.keys())} metrics")
        clone_index(source, target, name)

        if args.verbose:
            print(
                f"Found source buckets {', '.join([f'{k}({len(v)})' for k, v in buckets.items()])}"
            )

        for metric, ids in buckets.items():
            watcher.update(f"cloning metric {metric} with {len(ids)} ids")
            a = source.search(
                index=name,
                body={
                    "size": BIG,
                    "query": {"bool": {"filter": {"terms": {id_field: ids}}}},
                },
            )
            if args.verbose > 1:
                print(
                    f"Cloning {name} bucket {metric}: {len(ids)} "
                    f"IDs: {len(a['hits']['hits'])} found"
                )
            batches = []
            batch = 0
            total_ids += len(ids)
            if len(ids) > args.batch:
                while len(ids) > 0:
                    batches.append(ids[0 : args.batch])
                    ids = ids[args.batch :]
                if args.verbose > 1:
                    print(
                        f"Dividing {name} ({metric}) into {len(batches)} "
                        f"batches of {args.batch}"
                    )
            else:
                batches.append(ids)

            for b in batches:
                watcher.update(
                    f"cloning metric {metric}, batch {batch}: "
                    f"{total_ids} ids, {total_data} records"
                )
                batch += 1
                r = target.reindex(
                    body={
                        "source": {
                            "remote": remote,
                            "index": name,
                            "query": {
                                "bool": {"filter": {"terms": {id_field: b}}},
                            },
                        },
                        "dest": {"index": name},
                        "size": BIG,
                    },
                    timeout="5m",
                    request_timeout=10000.0,
                    wait_for_completion=True,
                    refresh=True,
                )
                total_data += r.get("total", 0)
                if r.get("failures"):
                    print(
                        f"Problem reindexing bucket {metric} (batch {batch}): {r}",
                        file=sys.stderr,
                    )
                    raise Exception(
                        f"I'm sorry, but {name}/{metric} resisted assimilation"
                    )
                elif args.verbose > 2:
                    print(f"Reindex {name} {metric} (batch {batch}): {r}")
                elif args.verbose:
                    print(f"Reindex {name} {metric} (batch {batch})")
    print(
        f"Done cloning {pattern} ({total_ids} metrics with {total_data} "
        f"documents): {time.time()-start:.3f} seconds"
    )


def snapshot(server: Elasticsearch):
    watcher.update("Creating snapshot functional:base")
    r = server.snapshot.create_repository(
        repository="functional",
        body={
            "type": "fs",
            "settings": {"location": "/var/tmp/snapshot"},
        },
    )
    if r.get("acknowledged") is not True:
        raise Exception(f"Opensearch didn't create the repository: {r}")
    r = server.snapshot.status(repository="functional", snapshot="base")
    if len(r["snapshots"]) == 0:
        if args.verbose:
            print("There are no functional test snapshots")
    else:
        if len(r["snapshots"]) != 1:
            raise Exception(
                "Unexpected snapshot status: expecting just 'base', "
                f"found {', '.join([i.snapshot for i in r['snapshots']])}"
            )
        snapshot = r["snapshots"][0]
        if snapshot["snapshot"] != "base" or snapshot["repository"] != "functional":
            raise Exception(
                "Unexpected snapshot: expect functional/base: "
                f"{snapshot['repository']}/{snapshot['snapshot']}"
            )
        r = server.snapshot.delete(repository="functional", snapshot="base")
        if r.get("acknowledged") is not True:
            raise Exception(f"Snapshot 'base' deletion failed with {r}")
        elif args.verbose:
            print(f"DELETE: {r}")
    r = server.snapshot.create(
        repository="functional",
        snapshot="base",
        body={
            "indices": "cdm*",
            "ignore_unavailable": True,
            "include_global_state": False,
        },
        wait_for_completion=True,
    )
    snap = r["snapshot"]
    if snap.get("failures"):
        raise Exception(f"Snapshot failures: {r['failures']}")
    if args.verbose > 1:
        print(f"SNAP: {snap}")
    indices = {i for i in snap["indices"] if i.startswith("cdm")}
    print("Created snapshot 'base' in repository 'functional'", file=sys.stderr)
    print(f" with indices: {indices}", file=sys.stderr)
    print(
        "\nYou need to pull it out of the container since you know the container name:",
        file=sys.stderr,
    )
    print(" podman exec -it <container> bash", file=sys.stderr)
    print("  cd /var/tmp", file=sys.stderr)
    print("  tar cfz snapshot.tar.gz snapshot", file=sys.stderr)
    print(" podman cp <container>:/var/tmp/snapshot.tar.gz .", file=sys.stderr)


parser = argparse.ArgumentParser("clone")
parser.add_argument("source", help="Source server address")
parser.add_argument("target", help="Target server address")
parser.add_argument(
    "-b",
    "--batch",
    dest="batch",
    default=2000,
    action="store",
    help="Break large sets into batches",
)
parser.add_argument(
    "-c", "--clone", dest="clone", action="store_true", help="Clone a database"
)
parser.add_argument(
    "-i",
    "--ids",
    dest="ids",
    help="Read a list of run IDs from the named file",
)
parser.add_argument(
    "-s",
    "--snapshot",
    dest="snapshot",
    action="store_true",
    help="Create a snapshot of the target",
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
parser.add_argument(
    "-w",
    "--watch",
    dest="watch",
    type=float,
    default=60.0,
    action="store",
    help="Periodically report status",
)

args = parser.parse_args()
print(f"SOURCE: {args.source}")
print(f"TARGET: {args.target}")

verifier = Verify(args.verbose)
watcher = Watch(args.watch)

try:
    ids = []
    if args.ids:
        try:
            ids = Path(args.ids).read_text().splitlines()
        except FileNotFoundError:
            print(f"File {args.ids} not found", file=sys.stderr)
            sys.exit(1)
        if args.verbose:
            print(f"Annointed runs: {ids}")
    source = open_opensearch(args.source)
    target = open_opensearch(args.target)
    print(f"SOURCE: {source.cluster.health()}")
    print(f"TARGET: {target.cluster.health()}")
    detect_versions(source)
    print(f"version: {VERSION}")
    if args.clone:
        clone(source, target, ids)
    if args.snapshot:
        snapshot(target)
    sys.exit(0)
except Exception as exc:
    if args.verbose:
        raise
    print(f"Something smells foul: {str(exc)!r}")
    sys.exit(1)
