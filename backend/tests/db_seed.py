import time

from urllib.parse import urlparse
from opensearchpy import OpenSearch, OpenSearchException, Search
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
    return OpenSearch(
        hosts = [{"host": host, "port": port}],
        http_compress = True,
        http_auth = (username, password),
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False
    )


def get_indices(client_):
    indices = client_.indices.get_alias(index="*")
    print(f"found indices {indices}")


def main():
    ok = False
    start = time.time()
    cfg = get_config()
    url = urlparse(cfg.get("ocp.elasticsearch.url"))

    while not ok:
      try:
          client_ = search_client(
              host=url.hostname,
              port=url.port,
              username=cfg.get("ocp.elasticsearch.username"),
              password=cfg.get("ocp.elasticsearch.password")
          )
          get_indices(client_)
          ok = True
          print(f"Opensearch ready after {time.time()-start:.3f} seconds")
      except OpenSearchException as exc:
          print(f"Opensearch isn't ready: {str(exc)!r}")
          time.sleep(4)
    
    seed_db(client_)


def query_ocp_index():
    cfg = get_config()              
    url = urlparse(cfg.get("ocp.elasticsearch.url"))
    client_ = search_client(
        host=url.hostname,
        port=url.port,
        username=cfg.get("ocp.elasticsearch.username"),
          password=cfg.get("ocp.elasticsearch.password")
    )
    q = {
      "size": 5,
      "query": {
          "match_all": {}
      }
    }
    s = Search(
        using=client_, index="perf_scale_ci",
    ).update_from_dict(q)
    for h in s:
        print(h)
    print(f'hits total {s.count()}')      


if __name__ == "__main__":
    main()
