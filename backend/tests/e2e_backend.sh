#!/bin/bash
set -e

echo "building backend image"
podman build -f backend/backend.containerfile --tag backend ./backend

echo "building backend functional test image"
podman build -f backend/tests/functional.containerfile --tag e2e-backend ./backend

export POD_NAME="e2e"

echo "cleaning up and recreating pod"
podman pod rm -f ${POD_NAME}
podman pod create --name=${POD_NAME} --publish 8000:8000

./backend/tests/opensearch_ocp.sh
echo "seeding db"
podman run --rm -it --pod=${POD_NAME} --entrypoint python3 e2e-backend tests/db_seed.py
podman run -d --pod=${POD_NAME} \
  -v "$(pwd)/backend/tests/ocpperf_test.toml:/backend/ocpperf.toml:z" \
  --name=back backend
