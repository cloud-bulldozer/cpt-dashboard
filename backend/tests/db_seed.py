import time

from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError, ConnectionError
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
    return True


def search_client(
        host: str = "localhost", port: int = "9200", 
        username: str = "admin", password: str = "admin"):
    return Elasticsearch(
        hosts = [{"host": host, "port": port}],
        http_compress = True,
        http_auth = (username, password),
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False
    )


def ocp_index_hits():
    cfg = get_config()              
    url = urlparse(cfg.get("ocp.elasticsearch.url"))
    client_ = search_client(
        host=url.hostname,
        port=url.port,
        username=cfg.get("ocp.elasticsearch.username"),
          password=cfg.get("ocp.elasticsearch.password")
    )
    response = client_.search(
       index=cfg.get("ocp.elasticsearch.indice"),
       body={
          "query": {
             "match_all": {}
          }
        }
    )
    
    if "hits" in response and "total" in response["hits"]:
       return response["hits"]["total"]["value"]
    return -1


def main():
    ok = False
    start = time.time()
    cfg = get_config()
    url = urlparse(cfg.get("ocp.elasticsearch.url"))
    seeded = False

    while not ok:
      try:
        client_ = search_client(
            host=url.hostname,
            port=url.port,
            username=cfg.get("ocp.elasticsearch.username"),
            password=cfg.get("ocp.elasticsearch.password")
        )
        response = client_.cluster.health(wait_for_status="yellow")
        print(f"cluster health: {response['status']}")

        if not seeded:
           seed_db(client_)
           seeded = True

        response = client_.indices.get_alias(index="*")
        print(f'test data index found: {cfg.get("ocp.elasticsearch.indice") in response.keys()}')
        print(f'at least 5 hits: {ocp_index_hits() >= 5}')       

        ok = True
        print(f"Opensearch ready after {time.time()-start:.3f} seconds")
        
      except (
            TransportError,
            ConnectionError,
      ) as exc:
        print(f"Opensearch isn't ready: {str(exc)!r}")
        time.sleep(3)


if __name__ == "__main__":
    main()
