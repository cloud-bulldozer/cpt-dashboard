# Something Quirky
OpenShift Container Platform Performance Dashboard


## Development on Local System

### Requires

* Python 3.9
* pipenv
* yarn

1. Follow [backend setup readme](backend/README.md)
2. Follow [frontend setup readme](frontend/README.md)


## Development in Containers

### Requires

* podman

### Build Backend

#### Requires

* pipenv  
* current working directory is `backend/app`

Build backend image.

    $ pipenv lock -r > requirements.txt

    $ podman build \
      --tag ocpp-back-i \
      --file backend.containerfile \
      .


### Run Backend 

Run the backend container and attach source code as a writable volume.

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD/app:/app:z" \
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
        --volume "$PWD/app:/app:z" \
        --pod ocpp-dev
        ocpp-back-i /app/scripts/start-reload.sh 

Open a second terminal. Go to the frontend directory.

Run frontend.

    $ podman run \
        --interactive \
        --tty \
        --volume "$PWD:/app:z" \
        --pod ocpp-dev \
        ocpp-front-dev-i


## Example Production Orchestration

This will build and run the backend and frontend containers, and expose their pod on port `8080`.

### Requires

* podman
* working directory is the repository root directory

```shell 
#!/bin/sh

cd backend
pipenv lock -r > requirements.txt
podman build . --tag ocpp-back-i

cd ../frontend
podman build . --tag ocpp-front-i

podman rm -f front back
podman pod rm -f ocpp
podman pod create --name ocpp --publish 8080:80

podman run -d --name=back --pod ocpp ocpp-back-i
podman run -d --name=front --pod ocpp ocpp-front-i
```