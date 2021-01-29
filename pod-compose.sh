#!/bin/sh

podman rm -f front back
podman pod rm -f ocpp
podman pod create --name ocpp --publish 8080:80

podman run -d --name=back --pod ocpp -v "$PWD/ocpperf.toml:/backend/ocpperf.toml" ocpp-back-i

podman run -d --name=front --pod ocpp ocpp-front-i