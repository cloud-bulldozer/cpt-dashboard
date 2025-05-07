#!/bin/bash
if [ ${DEBUG} ]; then set -ex ;fi

cleanup () {
    set +e
    echo "Cleaning up..."
    podman pod stop "${POD_NAME}"
    podman rm "${POD_NAME}-func" "${POD_NAME}-front" "${POD_NAME}-back" "${POD_NAME}-opensearch"
    podman pod rm "${POD_NAME}"
}

BRANCH="$(git rev-parse --show-toplevel)"
BACKEND="${BRANCH}/backend"
FRONTEND="${BRANCH}/frontend"
SETUP="${BACKEND}"/tests/functional/setup
CPT_CONFIG=${CPT_CONFIG:-"${SETUP}/funcconfig.toml"}
export POD_NAME=${POD_NAME:-FUNC${RANDOM}}

# DEVEL=1 backend/tests/functional/setup/test.sh
#
# In "DEVEL" mode, allow external access to the server port, and don't terminate
# the pod when this script exits.
if [ ${DEVEL} ]
then
    PUBLISH="--publish 127.0.0.1:8000:8000"
else
    PUBLISH=""
    trap cleanup EXIT
fi
podman pod create --name=${POD_NAME} ${PUBLISH}

${BACKEND}/scripts/version.py
podman build -f backend.containerfile --tag backend "${BACKEND}"
podman build -f frontend.containerfile --tag frontend "${FRONTEND}"
podman build -f tests/functional/setup/functional.containerfile --tag functional "${BACKEND}"

POD="--pod ${POD_NAME}"

"${SETUP}"/opensearch.sh
podman run -d ${POD} --name="${POD_NAME}-back" -v "${CPT_CONFIG}:/opt/backend/ocpperf.toml:Z" localhost/backend
podman run -d ${POD} --name="${POD_NAME}-front" localhost/frontend
podman run ${POD} --name="${POD_NAME}-func" localhost/functional

if [ ${DEVEL} ]
then
    echo -e "\n\n--------------\nWhen finished, type\n  podman pod stop ${POD_NAME}\n--------------"
fi
