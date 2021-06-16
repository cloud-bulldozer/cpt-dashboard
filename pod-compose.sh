#!/bin/sh

podman rm -f front back

podman run -d --name=back -p 8000:8000 -v "$PWD/backend/ocpperf.toml:/backend/ocpperf.toml" ocpp-back-i

podman run -d --name=front -p 3000:3000 ocpp-front-i
