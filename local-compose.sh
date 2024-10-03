#!/bin/sh
#
# Simple script to build and deploy the frontend and backend containers.
#
# Users must to update the backend/ocpperf.toml file to meet their needs.
#
# Please don't edit this file for debugging: it's too easy to accidentally
# commit undesirable changes. Instead, I've added some convenient environment
# variables to support common changes (customizing the container ports, and
# disabling either the front end or back end container):
#
# CPT_BACKEND_PORT -- set the port for the backend (default 8000)
# CPT_FRONTEND_PORT -- set the port for the UI (default 3000)
# SKIP_FRONTEND -- SKIP_FRONTEND=1 to skip building and running frontend
# SKIP_BACKEND -- SKIP_BACKEND=1 to skip building and running backend
#
CPT_BACKEND_PORT=${CPT_BACKEND_PORT:-8000}
CPT_FRONTEND_PORT=${CPT_FRONTEND_PORT:-3000}
CPT_CONFIG=${CPT_CONFIG:-"$PWD/backend/ocpperf.toml"}
SKIP_FRONTEND=${SKIP_FRONTEND:-0}
SKIP_BACKEND=${SKIP_BACKEND:-0}
podman rm -f front back

if [ "$SKIP_BACKEND" != 1 ] ;then
  podman build -f backend/backend.containerfile --tag backend
  podman run -d --name=back -p ${CPT_BACKEND_PORT}:8000 --network=host -v "${CPT_CONFIG}:/backend/ocpperf.toml:Z" localhost/backend
fi

if [ "$SKIP_FRONTEND" != 1 ] ;then
  podman build -f frontend/frontend.containerfile --tag frontend
  podman run -d --name=front --network=host -p ${CPT_FRONTEND_PORT}:3000 localhost/frontend
fi
