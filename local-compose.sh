#!/bin/sh
#
# Simple script to build the frontend and backend, and deploy to test changes
#
# Requirements/Assumptions:
# - Users will need to update the backend/ocpperf.toml file to meet their needs.
# - You must have both podman and docker installed: we use "podman compose".
#   However the podman compose engine isn't complete and won't work: but the
#   "podman compose" command uses the docker compose engine if installed, which
#   does work.
#
# Usage:
#   ./local-compose.sh
#
#   This will build the frontend and backend containers, and deploy them locally
#   to assist in development. Note that these containers don't react to source
#   changes, so `./run-local.sh` may be a better option for active development.
#
#   Also, as our real deployment is based on Kubernetes applications, services,
#   and routes, docker compose is not an accurate simulation of the real
#   deployment. An alternative is to set up a local minikube or OpenShift Local
#   and deploy there for testing -- instructions and scripting support TBD.
#
# Assisted-by: Cursor AI

TOP=$(git rev-parse --show-toplevel)
BACKEND=${TOP}/backend

podman compose --file ${TOP}/compose.yaml down

${BACKEND}/scripts/version.py

podman compose --file ${TOP}/compose.yaml build frontend-host backend-host
podman compose --file ${TOP}/compose.yaml up --detach frontend-host backend-host
