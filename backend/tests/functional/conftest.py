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
    ok = False
    start = time.time()
    while not ok:
        try:
            db = Elasticsearch("http://localhost:9200")
            r = db.indices.get("*")
            ok = True
        except Exception as exc:
            print(f"Opensearch isn't ready: {str(exc)!r}")
            time.sleep(5)
    print(f"Opensearch ready after {time.time()-start:.3f} seconds")
    cdm = {i for i in r.keys() if i.startswith("cdmv")}
    if cdm:
        print(f"CDM indices appear to be available: {','.join(cdm)}")
    else:
        # Opensearch hasn't been loaded yet, so restore the snapshot
        print("Restoring 'base' snapshot...")
        r = db.snapshot.create_repository(
            repository="functional",
            body={"type": "fs", "settings": {"location": "/var/tmp/snapshot"}},
        )
        assert r.get("acknowledged") is True
        r = db.snapshot.get(repository="functional", snapshot="base")
        # We expect one snapshot, named "base"
        assert r["snapshots"][0]["snapshot"] == "base"
        r = db.snapshot.restore(
            repository="functional",
            snapshot="base",
            body={"indices": "cdmv*dev-*"},
            wait_for_completion=True,
        )
        assert r["snapshot"]["shards"]["failed"] == 0
