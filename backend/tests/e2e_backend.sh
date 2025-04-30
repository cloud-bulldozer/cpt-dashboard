#!/bin/bash
set -e

TOP=$(git rev-parse --show-toplevel)
BACKEND=${TOP}/backend
cd ${BACKEND}

echo "generating version file"
scripts/version.py

echo "building backend image"
podman build -f backend.containerfile --tag backend .

echo "building backend functional test image"
podman build -f tests/functional.containerfile --tag functional .

export POD_NAME="e2e"

echo "cleaning up and recreating pod"
podman pod rm -f ${POD_NAME}
podman pod create --name=${POD_NAME} --publish 127.0.0.1:8000:8000 --publish 127.0.0.1:3000:3000

./tests/opensearch_ocp.sh
echo "seeding db"
podman run --rm --pod=${POD_NAME} --entrypoint python3 functional tests/db_seed.py
echo "deploying backend"
podman run -d --pod=${POD_NAME} \
  -v "${BACKEND}/tests/ocpperf_test.toml:/opt/backend/ocpperf.toml:z" \
  --name=back backend
