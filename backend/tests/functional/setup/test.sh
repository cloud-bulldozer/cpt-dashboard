#!/bin/bash
if [ ${DEBUG} ]; then set -ex ;fi

BRANCH="$(git rev-parse --show-toplevel)"
TESTING="${BRANCH}/testing"

. ${TESTING}/pod_setup.sh
CONTAINERS+=( "${POD_NAME}-func" )

podman run ${POD} --name="${POD_NAME}-func" localhost/functional
status=$?
echo "Functional test status ${status}"
if [[ $status -ne 0 ]] ;then
    podman logs "${POD_NAME}-back"
fi
