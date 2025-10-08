#!/bin/bash
# Build and run a backend container for testing.
#
# NOTE:
# This does not build or run the frontend. That would require additional
# framework to work around the NGINX dependency on the kubernetes backend
# service.
if [ ${DEBUG} ]; then set -ex ;fi

BRANCH="$(git rev-parse --show-toplevel)"
BACKEND="${BRANCH}/backend"
FRONTEND="${BRANCH}/frontend"
CPT_CONFIG=${CPT_CONFIG:-"${BACKEND}/ocpperf.toml"}
if [ ! -f "${CPT_CONFIG}" ]; then
    echo "Error: ${CPT_CONFIG} not found" >&2
    echo "Please update the ${CPT_CONFIG} file to meet your needs." >&2
    exit 1
fi

export CONTAINERS=()

cleanup () {
    set +e
    if [[ "${NOCLEANUP}" -ne 1 && "${#CONTAINERS[@]}" -ne 0 ]]
    then
        echo "Cleaning up..."
        podman stop "${CONTAINERS[@]}"
        podman rm "${CONTAINERS[@]}"
    else
        echo "Leaving pod ${POD_NAME} running for debug"
    fi
}

echo "Creating version"
( cd ${BACKEND}; poetry install ; poetry run scripts/version.py )
podman build -f backend.containerfile --tag backend "${BACKEND}"
echo "Starting backend container"
podman run -d --name="backend" -p 127.0.0.1:8000:8000 -v "${CPT_CONFIG}:/backend/ocpperf.toml:Z" localhost/backend
CONTAINERS=( "backend" )

echo -e "\n\n--------------\nWhen finished, type\n  podman rm --force ${CONTAINERS[@]}\n--------------"
