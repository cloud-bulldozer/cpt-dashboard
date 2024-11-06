#!/usr/bin/env python3
"""Set up Opensearch for functional tests

The functional test Opensearch instance has a "golden" snapshot called
"functional" in the designated snapshot directory. We need to call
Opensearch APIs to establish that snapshot repository and restore the
snapshot. Since the Opensearch is started in an isolated pod, we can't
script this from outside the pod; so we run this little Python program
inside the Opensearch container.
"""
import os
import time

from elasticsearch import Elasticsearch
import pytest


@pytest.fixture(scope="session")
def server():
    server = os.getenv("SERVER")
    assert server, "SERVER environment variable must be set"
    return server


@pytest.fixture(scope="session", autouse=True)
def restore_snapshot():

    def indices(db: Elasticsearch) -> set[str]:
        r = db.indices.get("*")
        cdm = {i for i in r.keys() if i.startswith("cdmv")}
        return cdm

    ok = False
    while not ok:
        time.sleep(5)
        try:
            start = time.time()
            db = Elasticsearch("http://localhost:9200")
            db.cluster.health(wait_for_status="green")
            print(f"Opensearch claims ready after {time.time()-start:.3f} seconds")
            ok = True
        except Exception as exc:
            print(f"Opensearch isn't ready: {type(exc).__name__} ({str(exc)!r})")
            continue

        r = db.indices.get("*")
        cdm = indices(db)
        if not cdm:
            try:
                # Opensearch hasn't been loaded yet, so restore the snapshot
                print("Restoring 'base' snapshot...")
                r = db.snapshot.create_repository(
                    repository="functional",
                    body={
                        "type": "fs",
                        "settings": {"location": "/var/tmp/snapshot"},
                    },
                )
                assert (
                    r.get("acknowledged") is True
                ), f"Opensearch didn't create the repository: {r}"
                r = db.snapshot.get(repository="functional", snapshot="base")
                # We expect one snapshot, named "base"
                assert (
                    r["snapshots"][0]["snapshot"] == "base"
                ), f"Opensearch didn't find our snapshot: {r}"
                r = db.snapshot.restore(
                    repository="functional",
                    snapshot="base",
                    request_timeout=20,
                    body={"indices": "cdmv*dev-*"},
                    wait_for_completion=True,
                    master_timeout="60s",
                )
                assert (
                    r["snapshot"]["shards"]["failed"] == 0
                ), f"Opensearch restore failed: {r}"
                cdm = indices(db)
            except Exception as exc:
                print(
                    f"Opensearch restore problem: {type(exc).__name__} ({str(exc)!r})"
                )
                raise
        print(f"Restored {len(cdm)} indices: {','.join(cdm)}")
        time.sleep(2)  # Paranoia: allow stabilization
        hits = db.search(index="cdmv7dev-run")
        ids = [h["_source"]["run"]["id"] for h in hits["hits"]["hits"]]
        print(f"Found run IDs {ids} ({len(ids)})")
        assert len(ids) == 5, "Expected CDM run documents are missing"
