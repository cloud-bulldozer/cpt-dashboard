from urllib.parse import urlparse

from opensearchpy import Opensearch

from vyper import v


CONTAINER_PATH_SNAPSHOT = "/var/tmp/snapshot"


def get_config():
    v.set_config_name("ocpperf_test")
    v.add_config_path(".")
    v.read_in_config()
    return v


def seed_db(srch_client):
    repo_name = "my_repository"
    snapshot_name = "my_snapshot"
    repo_body = {
      "type": "fs",
      "settings": {
        "location": CONTAINER_PATH_SNAPSHOT
      }
    }
    response = srch_client.snapshot.create_repository(
      repository=repo_name, body=repo_body
    )
    print(f"create repo: {response}")
    assert response["acknowledged"] is True
    response = srch_client.snapshot.restore(
      repository=repo_name, snapshot=snapshot_name
    )
    print(f"restore snapshot: {response}")
    assert response["accepted"] is True


def search_client(
        host: str = "localhost", port: int = "9200", 
        username: str = "admin", password: str = "admin"):
    return Opensearch(
        hosts = [{"host": host, "port": port}],
        http_compress = True,
        http_auth = (username, password),
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False
    )


def main():
    cfg = get_config()
    url = urlparse(cfg.get("ocp.elasticsearch.url"))
    seed_db(search_client(
        host=url.hostname,
        port=url.port,
        username=cfg.get("ocp.elasticsearch.username"),
        password=cfg.get("ocp.elasticsearch.password")
    ))


if __name__ == "__main__":
    main()
