#!/bin/bash
set -ex

cleanup () {
    set +e
    echo "Cleaning up..."
    podman pod stop "${POD_NAME}"
    podman rm "${POD_NAME}-e2e" "${POD_NAME}-front" "${POD_NAME}-back" "${POD_NAME}-opensearch"
    podman pod rm "${POD_NAME}"
}

BRANCH="$(git rev-parse --show-toplevel)"
BACKEND="${BRANCH}/backend"
FRONTEND="${BRANCH}/frontend"
SETUP="${BACKEND}"/tests/functional/setup
CPT_CONFIG=${CPT_CONFIG:-"${SETUP}/funcconfig.toml"}
export POD_NAME=${POD_NAME:-FUNC${RANDOM}}

podman pod create "${POD_NAME}"
trap cleanup EXIT

CYPRESS_POD="${POD_NAME}-e2e"

podman build -t frontend -f ${FRONTEND}/frontend.containerfile ${FRONTEND}
${BACKEND}/tests/e2e_backend.sh
podman run --pod=${POD_NAME} -d --name="${POD_NAME}-front" frontend
podman build -t e2e-frontend -f ${FRONTEND}/e2e_frontend.containerfile ${FRONTEND}
podman run --pod=${POD_NAME} --name=${CYPRESS_POD} e2e-frontend

# TODO: no screenshots to upload until e2e tests are remediated
# podman cp ${CYPRESS_POD}:/usr/src/cpt-dashboard/cypress/screenshots ${FRONTEND}/cypress/screenshots
