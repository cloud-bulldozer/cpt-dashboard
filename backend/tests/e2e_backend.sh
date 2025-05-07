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

export POD_NAME=${POD_NAME:-e2e}

pod_net=${POD_NAME:-e2e}
podman network remove --force $pod_net
podman network create $pod_net


./tests/opensearch_ocp.sh

echo "cleaning up and recreating pod"
podman pod rm -f ${POD_NAME}


echo "deploying backend"
podman run -d --pod=new:${POD_NAME}-pod-back \
  --network=${pod_net} \
  --publish 127.0.0.1:8000:8000 --publish 127.0.0.1:3000:3000 \
  -v "${BACKEND}/tests/ocpperf_test.toml:/opt/backend/ocpperf.toml:z" \
  --name="${POD_NAME}-back" backend

echo "seeding db"
podman run --rm --pod=${POD_NAME}-pod-back --network=${pod_net} --entrypoint python3 functional tests/db_seed.py
