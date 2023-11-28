# OpenShift Performance Dashboard

## Elasticsearch configuration

### Requires

* current working directory is `backend/`

Create a configuration file, named **ocpperf** with the following key structure, and fill in the values:

```toml
[<product>.elasticsearch]
url=
indice=
username=
password=

[ocp-server]
port=8000

[airflow]
url=
username=
password=
```

The elasticsearch configuration should be set up by product, that way each product can configure their own ES server.

As an example for `OCP` the configuration looks like this:

```toml
[ocp.elasticsearch]
url=
indice=
username=
password=
```

Internally the API when serving the `/ocp` enpoints will use this connection.

[TOML](https://toml.io/en/) is used above, but it also accepts YAML.


## Development on System

1. Follow [backend setup readme](backend/README.md)
2. Follow [frontend setup readme](frontend/README.md)


## Development in Containers

### Requires

* podman

### Build Backend

#### Requires

* current working directory is `backend/`

Build backend image.

    $ podman build \
      --tag ocpp-back \
      --file backend.containerfile \
      .


### Run Backend

Run the backend container and attach source code as a writable volume.

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD/app:/backend/app:z" \
        --volume "$PWD/ocpperf.toml:/backend/ocpperf.toml"
        --publish 8000:8000 \
        ocpp-back /backend/scripts/start-reload.sh


### Build Frontend

#### Requires

* current working directory is `frontend/`

Build frontend image.

    $ podman build \
        --tag ocpp-front \
        --file frontend-dev.containerfile \
        .

### Run Frontend

#### Requires

* second terminal
* current working directory is `frontend/`

Run frontend container and attach source code as a writable volume.

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD:/app:z" \
        --publish 3000:3000 \
        ocpp-front
