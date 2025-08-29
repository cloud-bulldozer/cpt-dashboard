#!/bin/bash
# NOTE: this helper should be *sourced* in the same shell in order to take
# advantage of the POD and POD_NAME definitions as well as the common cleanup
# handler.
if [ ${DEBUG} ]; then set -ex ;fi

BRANCH="$(git rev-parse --show-toplevel)"
BACKEND="${BRANCH}/backend"
FRONTEND="${BRANCH}/frontend"
TESTING="${BRANCH}/testing"
CPT_CONFIG=${CPT_CONFIG:-"${TESTING}/funcconfig.toml"}
export POD_NAME=${POD_NAME:-FUNC${RANDOM}}

export CONTAINERS=()

cleanup () {
    set +e
    if [[ "${NOCLEANUP}" -ne 1 ]]
    then
        echo "Cleaning up..."
        podman pod stop "${POD_NAME}"
        podman rm "${CONTAINERS[@]}"
        podman pod rm "${POD_NAME}"
    else
        echo "Leaving pod ${POD_NAME} running for debug"
    fi
}

# DEVEL=1 backend/tests/functional/setup/test.sh
#
# "DEVEL" mode allows testing a development server and frontend against the
# "canned" OpenSearch datasets. By default we'll start and initialize the
# OpenSearch backends, and initialize them from the functional test snapshots;
# you can run `backend/scripts/start-reload.sh` to start the backend and the
# usual `npm --prefix frontend run dev` for the frontend.
#
# FRONTDEVEL=1 DEVEL=1
#
# If you're only trying to debug the frontend code, adding FRONTDEVEL=1 will
# start the server inside the test pod and export the server port. Use the
# normal `npm --prefix frontend run dev` to test against it.
if [[ "${DEVEL}" -eq 1 || "${FRONTDEVEL}" -eq 1 ]]
then
    if [[ "${FRONTDEVEL}" -ne 1 ]]
    then
        echo "DEVEL mode set: publishing OpenSearch ports"
        echo "Run backend using 'backend/scripts/start-reload.sh' to debug"
        PUBLISH="--publish 127.0.0.1:9200:9200 --publish 127.0.0.1:9500:9500"
    else
        echo "FRONTDEVEL DEVEL mode set: publishing backend port"
        echo "Run frontend using 'npm --prefix frontend run dev'"
        PUBLISH="--publish 127.0.0.1:8000:8000"
    fi
else
    echo "ISOLATED CI mode set: no externally published ports"
    echo "Run test containers inside pod ${POD_NAME}"
    PUBLISH=""
    trap cleanup EXIT
fi

echo "Creating pod ${POD_NAME}"
podman pod create --name=${POD_NAME} ${PUBLISH}

echo "Creating version"
( cd ${BACKEND}; poetry install; poetry install; poetry run scripts/version.py )
podman build -f backend.containerfile.in --build-arg CA_CERT_PATH="" --tag backend "${BACKEND}"
podman build -f frontend.containerfile --tag frontend "${FRONTEND}"
podman build -f ${TESTING}/functional.containerfile --tag functional "${BRANCH}"

export POD="--pod ${POD_NAME}"

CONTAINERS=( "${POD_NAME}-front" "${POD_NAME}-back" \
        "${POD_NAME}-opensearch-ilab" "${POD_NAME}-opensearch-ocp" "${POD_NAME}-init" )
COMPONENT=ocp "${TESTING}"/opensearch.sh
COMPONENT=ilab OPENSEARCH_PORT=9500 "${TESTING}"/opensearch.sh
podman run ${POD} --name="${POD_NAME}-init" -v "${CPT_CONFIG}:/backend/ocpperf.toml:Z" --workdir /backend --entrypoint '["poetry", "run", "/backend/db_seed.py"]' localhost/functional
if [[ "${DEVEL}" -ne 1 || "${FRONTDEVEL}" -eq 1 ]]
then
    echo "Starting backend container"
    podman run -d ${POD} --name="${POD_NAME}-back" -v "${CPT_CONFIG}:/backend/ocpperf.toml:Z" localhost/backend
fi
if [[ "${DEVEL}" -ne 1 && "${FRONTDEVEL}" -ne 1 ]]
then
    echo "Starting frontend container"
    podman run -d ${POD} --name="${POD_NAME}-front" localhost/frontend
fi

if [[ "${DEVEL}" -eq 1 ]]
then
    echo -e "\n\n--------------\nWhen finished, type\n  podman pod stop ${POD_NAME}\n--------------"
fi
