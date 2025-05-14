#!/bin/sh
#
# Simple script to build the frontend and backend, and deploy to test out the changes
# Need:
# - Users will need to update the backend/ocpperf.toml file to meet their needs.
#
#
TOP=$(git rev-parse --show-toplevel)
BACKEND=${TOP}/backend

podman compose --file ${TOP}/compose.yaml down

${BACKEND}/scripts/version.py

podman compose --file ${TOP}/compose.yaml build
podman compose --file ${TOP}/compose.yaml up --detach
