#!/bin/sh
#
# Simple script to build the frontend and backend, and deploy to test out the changes
# Need:
# - Users will need to update the backend/ocpperf.toml file to meet their needs.
#
#
CPT_BACKEND_PORT=${CPT_BACKEND_PORT:-8000}
CPT_FRONTEND_PORT=${CPT_FRONTEND_PORT:-3000}
CPT_CONFIG=${CPT_CONFIG:-"$PWD/backend/ocpperf.toml"}
podman rm -f front back

podman build -f backend/backend.containerfile --tag backend
# podman build -f frontend/frontend.containerfile --tag frontend

# NOTE: add --network=host to test against a local containerized Horreum
podman run -d --name=back -p ${CPT_BACKEND_PORT}:8000 --network=host -v "${CPT_CONFIG}:/backend/ocpperf.toml:Z" localhost/backend

# podman run -d --name=front --net=host -p ${CPT_FRONTEND_PORT}:3000 localhost/frontend


