#!/usr/bin/env python3
import sys
import time
from dataclasses import dataclass
from typing import Optional

from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError, TransportError
from vyper import v


@dataclass
class Data:
    name: str
    config_prefix: str
    repo: str
    snapshot: str
    index_prefix: Optional[str] = None
    verify: Optional[dict[str, int]] = None


CONTAINER_PATH_SNAPSHOT = "/var/tmp/snapshot"
INTIALIZATIONS = [
    Data("ocp", "ocp.elasticsearch", "my_repository", "my_snapshot"),
    Data("ilab", "ilab.crucible", "functional", "base", index_prefix="cdm*"),
]


class Restore:

    def __init__(self, config_path: str):
        self.url = v.get(config_path + ".url")
        self.user = v.get(config_path + ".username")
        self.pwd = v.get(config_path + ".password")
        self.client = OpenSearch(
            self.url,
            basic_auth=(self.user, self.pwd) if self.user else None,
            verify_certs=False,
            ssl_show_warn=False,
        )
        start = time.time()
        ok = False
        while not ok:
            try:
                response = self.client.cluster.health(wait_for_status="green")
                print(
                    f"OpenSearch health is {response['status']} after {time.time()-start:.3f} seconds"
                )
                ok = True
            except (TransportError, ConnectionError) as exc:
                print(f"OpenSearch isn't ready: {type(exc).__name__} ({str(exc)!r})")
                time.sleep(4.0)
                continue

    def indices(self, prefix: str = "") -> set[str]:
        r = self.client.indices.get(prefix + "*")
        cdm = {i for i in r.keys()}
        return cdm

    def create_repo(self, repo: str, snapshot: str):
        r = self.client.snapshot.create_repository(
            repository=repo,
            body={
                "type": "fs",
                "settings": {"location": "/var/tmp/snapshot"},
            },
        )
        if r.get("acknowledged") is not True:
            raise Exception(f"Opensearch didn't create the repository: {r}")
        r = self.client.snapshot.get(repository=repo, snapshot="*")
        # We expect one snapshot, with the proper name
        if r["snapshots"][0]["snapshot"] != snapshot:
            raise Exception(f"Opensearch didn't find snapshot {snapshot}: {r}")

    def restore(
        self, repo: str, snapshot: str, prefix: Optional[str] = None
    ) -> set[str]:
        pattern = "*" if not prefix else prefix + "*"
        r = self.client.snapshot.restore(
            repository=repo,
            snapshot=snapshot,
            request_timeout=20,
            body={"indices": pattern},
            wait_for_completion=True,
            master_timeout="60s",
        )
        if r["snapshot"]["shards"]["failed"] != 0:
            raise Exception(f"Opensearch restore failed: {r}")
        return self.indices(pattern)


def ocp_index_hits(client_, ocp_index):
    response = client_.search(index=ocp_index, body={"query": {"match_all": {}}})
    if "hits" in response and "total" in response["hits"]:
        return response["hits"]["total"]["value"]
    return -1


def main() -> int:
    start = time.time()

    # Set up the configuration
    v.set_config_name("ocpperf")
    v.add_config_path(".")
    v.read_in_config()

    for db in INTIALIZATIONS:
        print(f"Restoring {db.name}: {db.repo}/{db.snapshot}")
        back = Restore(db.config_prefix)
        idx = (
            db.index_prefix if db.index_prefix else v.get(db.config_prefix + ".indices")
        )
        if idx is None:
            idx = ""
        got_index = back.indices(idx)
        print(f"{db.name}: found indices {got_index}")
        if not got_index:
            back.create_repo(db.repo, db.snapshot)
            back.restore(db.repo, db.snapshot, db.index_prefix)
            got_index = back.indices(idx)
            print(f"{db.name}: restored indices {got_index}")
        if not got_index:
            raise Exception(f"No matching indices were restored for {db.name}")

    dbs = [db.name for db in INTIALIZATIONS]
    print(f"Databases {', '.join(dbs)} ready after {time.time()-start:.3f} seconds")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"db_seed error: {str(exc)!r}")
        sys.exit(1)
