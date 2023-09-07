#!/bin/sh
#
# Simple script to build the frontend and backend, and deploy to test out the changes
# Need:
# - Users will need to update the backend/ocpperf.toml file to meet their needs.
#
#
podman rm -f front back

podman build -f backend/backend.containerfile --tag backend
podman build -f frontend/frontend.containerfile --tag frontend

podman run -d --name=back -p 8000:8000 -v "$PWD/backend/ocpperf.toml:/backend/ocpperf.toml:Z" localhost/backend

podman run -d --name=front -p 3000:3000 localhost/frontend
