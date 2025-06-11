#!/usr/bin/env python3
"""Fix broken Crucible CDM v7 Opensearch snapshot

I copied only templates rather than mappings from the production Crucible
instance, resulting in unusable data.

This will work against a restored snapshot (relying on the functional test
fixture) to clone each index using correct mappings, and then create a new
snapshot.

This specific code shouldn't be needed again, but the pattern may prove
useful.

E.g.:
    python3 tests/utilities/fix_snapshot.py http://localhost:9200
"""

import argparse
from collections import defaultdict
import json
import sys
import time
from typing import Any

from elasticsearch import Elasticsearch

# Conventional CDM query limit
SIZE: int = 262144


# The CDMv7 "root" index names
INDICES: tuple[str, ...] = (
    "run",
    "iteration",
    "sample",
    "period",
    "tag",
    "param",
    "metric_desc",
    "metric_data",
)


# The expected Opensearch index mappings for each CDMv7 index
MAPPINGS: dict[str, dict[str, Any]] = {
    "cdmv7dev-period": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "iteration": {
                "properties": {
                    "id": {"type": "keyword"},
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "primary-metric": {"type": "keyword"},
                    "primary-period": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "period": {
                "properties": {
                    "begin": {"type": "date"},
                    "end": {"type": "date"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "prev_id": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
            "sample": {
                "properties": {
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
        },
    },
    "cdmv7dev-param": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "iteration": {
                "properties": {
                    "id": {"type": "keyword"},
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "primary-metric": {"type": "keyword"},
                    "primary-period": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "param": {
                "properties": {
                    "arg": {"type": "keyword"},
                    "val": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
        },
    },
    "cdmv7dev-iteration": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "iteration": {
                "properties": {
                    "id": {"type": "keyword"},
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "primary-metric": {"type": "keyword"},
                    "primary-period": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
        },
    },
    "cdmv7dev-metric_data": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "metric_data": {
                "properties": {
                    "begin": {"type": "date"},
                    "duration": {"type": "long"},
                    "end": {"type": "date"},
                    "value": {"type": "double"},
                }
            },
            "metric_desc": {"properties": {"id": {"type": "keyword"}}},
            "run": {"properties": {"id": {"type": "keyword"}}},
        },
    },
    "cdmv7dev-sample": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "iteration": {
                "properties": {
                    "id": {"type": "keyword"},
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "primary-metric": {"type": "keyword"},
                    "primary-period": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
            "sample": {
                "properties": {
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
        },
    },
    "cdmv7dev-tag": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
            "tag": {
                "properties": {
                    "name": {"type": "keyword"},
                    "val": {"type": "keyword"},
                }
            },
        },
    },
    "cdmv7dev-run": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
        },
    },
    "cdmv7dev-metric_desc": {
        "dynamic": "strict",
        "properties": {
            "cdm": {
                "properties": {
                    "doctype": {"type": "keyword"},
                    "ver": {"type": "keyword"},
                }
            },
            "iteration": {
                "properties": {
                    "id": {"type": "keyword"},
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "primary-metric": {"type": "keyword"},
                    "primary-period": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "metric_desc": {
                "properties": {
                    "class": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "names": {
                        "properties": {
                            "action": {"type": "keyword"},
                            "actions": {"type": "keyword"},
                            "batch": {"type": "keyword"},
                            "benchmark-group": {"type": "keyword"},
                            "benchmark-id": {"type": "keyword"},
                            "benchmark-name": {"type": "keyword"},
                            "benchmark-role": {"type": "keyword"},
                            "blade": {"type": "keyword"},
                            "bridge": {"type": "keyword"},
                            "cgroup": {"type": "keyword"},
                            "class": {"type": "keyword"},
                            "clientserver": {"type": "keyword"},
                            "cluster": {"type": "keyword"},
                            "cmd": {"type": "keyword"},
                            "container": {"type": "keyword"},
                            "controller": {"type": "keyword"},
                            "cookie": {"type": "keyword"},
                            "core": {"type": "keyword"},
                            "counter": {"type": "keyword"},
                            "cpu": {"type": "keyword"},
                            "csid": {"type": "keyword"},
                            "cstype": {"type": "keyword"},
                            "ct_label": {"type": "keyword"},
                            "ct_mark": {"type": "keyword"},
                            "ct_state": {"type": "keyword"},
                            "ct_zone": {"type": "keyword"},
                            "desc": {"type": "keyword"},
                            "dev": {"type": "keyword"},
                            "die": {"type": "keyword"},
                            "direction": {"type": "keyword"},
                            "dl_dst": {"type": "keyword"},
                            "dl_src": {"type": "keyword"},
                            "dl_vlan": {"type": "keyword"},
                            "domain": {"type": "keyword"},
                            "dp": {"type": "keyword"},
                            "dp_hash": {"type": "keyword"},
                            "dport": {"type": "keyword"},
                            "dst": {"type": "keyword"},
                            "endpoint-label": {"type": "keyword"},
                            "engine-id": {"type": "keyword"},
                            "engine-role": {"type": "keyword"},
                            "engine-type": {"type": "keyword"},
                            "epoch": {"type": "keyword"},
                            "error": {"type": "keyword"},
                            "eth_dst": {"type": "keyword"},
                            "eth_src": {"type": "keyword"},
                            "eth_type": {"type": "keyword"},
                            "flags": {"type": "keyword"},
                            "group": {"type": "keyword"},
                            "host": {"type": "keyword"},
                            "hosted-by": {"type": "keyword"},
                            "hostname": {"type": "keyword"},
                            "hypervisor-host": {"type": "keyword"},
                            "icmp_code": {"type": "keyword"},
                            "icmp_type": {"type": "keyword"},
                            "id": {"type": "keyword"},
                            "in_port": {"type": "keyword"},
                            "interface": {"type": "keyword"},
                            "interface-type": {"type": "keyword"},
                            "ipv4_dst": {"type": "keyword"},
                            "ipv4_frag": {"type": "keyword"},
                            "ipv4_proto": {"type": "keyword"},
                            "ipv4_src": {"type": "keyword"},
                            "ipv6_dst": {"type": "keyword"},
                            "ipv6_src": {"type": "keyword"},
                            "irq": {"type": "keyword"},
                            "job": {"type": "keyword"},
                            "kthread": {"type": "keyword"},
                            "level": {"type": "keyword"},
                            "mark": {"type": "keyword"},
                            "metadata": {"type": "keyword"},
                            "mode": {"type": "keyword"},
                            "node": {"type": "keyword"},
                            "num": {"type": "double"},
                            "osruntime": {"type": "keyword"},
                            "output": {"type": "keyword"},
                            "package": {"type": "keyword"},
                            "parent": {"type": "keyword"},
                            "pid": {"type": "keyword"},
                            "pod": {"type": "keyword"},
                            "port": {"type": "keyword"},
                            "port_pair": {"type": "keyword"},
                            "priority": {"type": "keyword"},
                            "protocol": {"type": "keyword"},
                            "rank": {"type": "keyword"},
                            "recirc_id": {"type": "keyword"},
                            "reg14": {"type": "keyword"},
                            "role": {"type": "keyword"},
                            "rx_port": {"type": "keyword"},
                            "skb_mark": {"type": "keyword"},
                            "skb_priority": {"type": "keyword"},
                            "slot": {"type": "keyword"},
                            "socket": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "sport": {"type": "keyword"},
                            "src": {"type": "keyword"},
                            "status": {"type": "keyword"},
                            "step": {"type": "keyword"},
                            "stream": {"type": "keyword"},
                            "table": {"type": "keyword"},
                            "tcp_dst": {"type": "keyword"},
                            "tcp_src": {"type": "keyword"},
                            "thread": {"type": "keyword"},
                            "tid": {"type": "keyword"},
                            "tier": {"type": "keyword"},
                            "tool-name": {"type": "keyword"},
                            "tx_port": {"type": "keyword"},
                            "type": {"type": "keyword"},
                            "udp_dst": {"type": "keyword"},
                            "udp_src": {"type": "keyword"},
                            "ufid": {"type": "keyword"},
                            "use": {"type": "keyword"},
                            "userenv": {"type": "keyword"},
                            "vlan": {"type": "keyword"},
                        }
                    },
                    "names-list": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "value-format": {"type": "keyword"},
                    "values": {
                        "properties": {
                            "fail": {"type": "keyword"},
                            "pass": {"type": "keyword"},
                        }
                    },
                }
            },
            "period": {
                "properties": {
                    "begin": {"type": "date"},
                    "end": {"type": "date"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "prev_id": {"type": "keyword"},
                }
            },
            "run": {
                "properties": {
                    "begin": {"type": "date"},
                    "benchmark": {"type": "keyword"},
                    "desc": {"type": "text", "analyzer": "standard"},
                    "email": {"type": "keyword"},
                    "end": {"type": "date"},
                    "harness": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "whitespace",
                    },
                }
            },
            "sample": {
                "properties": {
                    "num": {"type": "unsigned_long"},
                    "path": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
        },
    },
}


# Translate from "root" index name to full CDMv7 index
def index(root: str) -> str:
    """Produce full index name

    Expand the CDM root index string to a full CDMv7 index name

    Args:
        root:   root index name

    Returns:
        full CDMv7 index name
    """
    return f"cdmv7dev-{root}"


def reindex(db: Elasticsearch, source: str, dest: str, raw: bool = False):
    """Reindex with proper mappings

    For each CDMv7 index, correct to use the proper mappings. This can't be
    done directly; Opensearch doesn't allow changing the mappings of existing
    documents. Instead, we'll reindex all documents into a scratch index, and
    then move them back to the correct index, with proper mappings.

    The size of the `metric_data` index makes this problematic, so approach
    that as a special case, breaking it down by individual metric description
    "sources". This should be a straightforward aggregation query; however the
    whole point here is that aggregations don't work on the default text field
    mapping, so we have to do it the hard way. Luckily we only need to do this
    once.

    Args:
        db: The Elasticsearch instance to use
        source: The source index name
        dest: The destination index name
        raw: The point is to add mappings to the indices -- if "raw" is True,
            assume that the source isn't mapped: all fields are "text" type
            with a ".keyword" sub-field we'll use for searches.
    """
    if "metric_data" in source:
        buckets = defaultdict(list)

        r = db.search(size=SIZE, index=index("metric_desc"))

        if args.verbose:
            print(f"Metric data: found {len(r['hits']['hits'])} descriptors")
        for h in r["hits"]["hits"]:
            s = h["_source"]["metric_desc"]
            buckets[f"{s['source']}::{s['type']}"].append(s["id"])

        if args.verbose:
            print(
                f"Found source buckets {', '.join([f'{k}({len(v)})' for k, v in buckets.items()])}"
            )

        field = "metric_desc.id"
        if raw:
            field += ".keyword"
        for name, ids in buckets.items():
            a = db.search(
                index=source,
                body={
                    "size": SIZE,
                    "query": {"bool": {"filter": {"terms": {field: ids}}}},
                },
            )
            print(
                f"Reindexing {source} bucket {name}: {len(ids)} IDs: {len(a['hits']['hits'])} found"
            )
            batches = []
            batch = 0
            if len(ids) > args.batch:
                while len(ids) > 0:
                    batches.append(ids[0 : args.batch])
                    ids = ids[args.batch :]
                if args.verbose:
                    print(
                        f"Dividing {source} ({name}) into {len(batches)} batches of {args.batch}"
                    )
            else:
                batches.append(ids)

            for b in batches:
                batch += 1
                r = db.reindex(
                    body={
                        "source": {
                            "index": source,
                            "query": {
                                "bool": {"filter": {"terms": {field: b}}},
                            },
                        },
                        "dest": {"index": dest},
                        "size": SIZE,
                    },
                    timeout="5m",
                    request_timeout=10000.0,
                    wait_for_completion=True,
                    refresh=True,
                    slices="auto",
                )
                if r.get("failures"):
                    print(
                        f"Problem reindexing bucket {name} (batch {batch}): {r}",
                        file=sys.stderr,
                    )
                elif args.verbose:
                    print(
                        f"Reindex {name} (batch {batch}) from {source} to {dest}: {r}"
                    )
    else:
        # Reindex the data in one batch for all other indices
        r = db.reindex(
            body={
                "source": {"index": source},
                "dest": {"index": dest},
                "size": SIZE,
            },
            timeout="5m",
            request_timeout=10000.0,
            wait_for_completion=True,
            refresh=True,
            slices="auto",
        )
        if r.get("failures"):
            print(f"Problem reindexing {source} to {dest}: {r}", file=sys.stderr)
            raise Exception(f"Reindexing {source} has failed: {r['failures']}")
        elif args.verbose:
            print(f"Reindex {source} to {dest}: {r}")
    if args.verbose:
        r = db.search(index=dest, body={"size": SIZE})
        print(
            f"Successfully reindexed {len(r['hits']['hits'])} entries "
            f"from {source} to {dest}"
        )


def repair(source: Elasticsearch):
    """Repair a CDMv7 database

    The original CDMv7 ILAB snapshot was created from a clone without the proper
    settings and mappings. This will repair the snapshot by moving data to a
    new index with proper configuration.

    This should only be necessary once -- including the script in the repo may
    provide useful information for future development.
    """
    tmp_indices = []
    for i in INDICES:
        start = time.time()
        name = index(i)
        tmp_name = name + "1"
        tmp_indices.append(tmp_name)
        print(f"Updating {name} through {tmp_name}")

        # 1. Reindex all the data to a new index
        # 2. Delete the original index
        # 3. Create the original index with proper settings & mappings
        # 4. Reindex all the data to the new "original" index

        r = source.search(index=name, body={"size": SIZE})
        original_count = len(r["hits"]["hits"])
        print(f"Previously {original_count} documents in {name}")

        # Create a new index -- we don't really need the mappings here,
        # but we need the max_result_window to enable the reindex.
        r = source.indices.create(
            tmp_name,
            body={
                "mappings": MAPPINGS[name],
                "settings": {"index": {"max_result_window": 262144}},
            },
        )
        if not r.get("acknowledged"):
            print(f"Failure creating {tmp_name}: {r}", file=sys.stderr)
        elif args.verbose:
            print(f"Create index {tmp_name}: {r}")

        reindex(source, name, tmp_name, raw=True)

        # Delete the original
        r = source.indices.delete(name, ignore_unavailable=True)
        if not r["acknowledged"]:
            print(f"delete {name} failed: {r}", file=sys.stderr)
            continue
        elif args.verbose:
            print(f"Sucessfully removed the original {name}")

        # Re-create the original index with proper settings and mappings
        r = source.indices.create(
            name,
            body={
                "mappings": MAPPINGS[name],
                "settings": {"index": {"max_result_window": 262144}},
            },
        )
        if not r.get("acknowledged"):
            print(f"Failure creating {name}: {r}", file=sys.stderr)
        elif args.verbose:
            print(f"Successfully created the new {name}")

        reindex(source, tmp_name, name)
        r = source.search(index=name, body={"size": SIZE})
        new_count = len(r["hits"]["hits"])
        if new_count != original_count:
            raise Exception(
                f"Houston, we have a problem: transferred {new_count} != {original_count}"
            )
        print(f"Done migrating {name}: {time.time()-start:.3f} seconds")
    for tmp in tmp_indices:
        r = source.indices.delete(tmp, ignore_unavailable=True)
        if not r["acknowledged"]:
            print(f"delete {tmp} failed: {r}", file=sys.stderr)
            continue
        elif args.verbose:
            print(f"Successfully deleted {tmp}")


def snapshot(server: Elasticsearch):
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
        print(
            f"Indices: {', '.join([str(i) for i in snapshot['indices'].keys() if i.startswith('cdm')])}"
        )
        r = server.snapshot.delete(repository="functional", snapshot="base")
        if r.get("acknowledged") is not True:
            raise Exception(f"Snapshot 'base' deletion failed with {r}")
        elif args.verbose:
            print(f"DELETE: {r}")
    r = server.snapshot.create(
        repository="functional", snapshot="base", wait_for_completion=True
    )
    snap = r["snapshot"]
    if snap.get("failures"):
        raise Exception(f"Snapshot failures: {r['failures']}")
    print(f"SNAP: {snap}")
    indices = {i for i in snap["indices"] if i.startswith("cdm")}
    expected = {index(i) for i in INDICES}
    if indices != expected:
        print(f"Expected indices {expected}")
        print(f"Actual indices: {indices}")
        raise Exception("The actual snapshotted indices differ from expected")


parser = argparse.ArgumentParser("clone")
parser.add_argument("server", help="Crucible Opensearch server address")
parser.add_argument(
    "-b",
    "--batch",
    dest="batch",
    default=1000,
    action="store",
    help="Break large sets into batches",
)
parser.add_argument(
    "-r", "--repair", dest="repair", action="store_true", help="Repair database"
)
parser.add_argument(
    "-s", "--snapshot", dest="snapshot", action="store_true", help="Replace snapshot"
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
if args.verbose:
    print(f"SOURCE: {args.server}")

try:
    server = Elasticsearch(args.server)
    if args.repair:
        repair(server)
    if args.snapshot:
        snapshot(server)
    sys.exit(0)
except Exception as exc:
    if args.verbose:
        raise
    print(f"Something smells odd: {str(exc)!r}")
    sys.exit(1)
