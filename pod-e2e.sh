#!/bin/bash
set -e

# echo "building backend test image"
# podman build -f backend/tests/e2e_backend.containerfile --tag e2e-backend ./backend

# POD_NAME="pod_e2e"

# echo "cleaning up and recreating pod"
# podman pod rm -f ${POD_NAME}
# podman pod create --name=${POD_NAME} --publish 8000:8000 --publish 9200:9200

# POD_NAME="pod_e2e" ./backend/tests/opensearch_ocp.sh
# podman run -d --pod=${POD_NAME} --name=back e2e-backend
# echo "seeding db"
# podman exec back poetry run python tests/db_seed.py

# ./backend/tests/e2e_backend.sh

echo "building frontend test image"
podman build -f frontend/e2e_frontend.containerfile --tag e2e-frontend ./frontend

# npm run --prefix frontend cypress:run:ci

podman run --rm -it --pod=${POD_NAME} --name=front e2e-frontend
exit $?