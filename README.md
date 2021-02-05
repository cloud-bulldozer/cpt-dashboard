# OpenShift Performance Dashboard



## Elasticsearch configuration

### Requires

* `pwd` is `backend/`

Create a configuration file, named **ocperf** with the following key structure, and fill in the values:

```toml
[elasticsearch]
url=
indice=
username=
password=

[ocp-server]
port=
```

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
      --tag ocpp-back-i \
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
        ocpp-back-i /scripts/start-reload.sh


### Build Frontend

#### Requires

* current working directory is `frontend`

Build frontend image.

    $ podman build \
        --tag ocpp-front-dev-i \
        --file frontend-dev.containerfile \
        .

### Run Frontend and Backend

Create a pod for communication between containers.

    $ podman pod create --name=ocpp-dev --publish 8000:3000

Go to the backend directory.

Run backend.

    $ cd backend

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD/app:/backend/app:z" \
        --volume "$PWD/ocpperf.toml:/backend/ocpperf.toml"
        --publish 8000:8000 \
        ocpp-back-i /scripts/start-reload.sh

Open a second terminal. Go to the frontend directory.

Run frontend.

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD:/app:z" \
        --pod ocpp-dev \
        ocpp-front-dev-i


## Example Production Orchestration

**Work In Progress**

~~This will build and run the backend and frontend containers, and expose their pod on port `8080`. You should see the frontend at `localhost:8080` in a web browser.~~

### ~~Requires~~

~~podman~~  
~~working directory is the repository root directory~~


