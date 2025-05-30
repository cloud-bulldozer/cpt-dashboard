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
import requests

import pytest


@pytest.fixture(scope="session")
def server():
    server = os.getenv("SERVER")
    assert server, "SERVER environment variable must be set"
    start = time.time()
    ok = False
    waited = False
    while not ok:
        try:
            requests.get(f"{server}/api/version")
            ok = True
        except Exception as exc:
            if (time.time() - start) > 60.0:
                assert False, f"Waited over a minute for server to start: {str(exc)!r})"
            time.sleep(1.0)
            waited = True
            continue
    if waited:
        print(f"(waited {time.time()-start:0.3f} seconds for server)", end="")
    return server
