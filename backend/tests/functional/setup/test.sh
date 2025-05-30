#!/bin/bash
if [ ${DEBUG} ]; then set -ex ;fi

BRANCH="$(git rev-parse --show-toplevel)"
TESTING="${BRANCH}/testing"

. ${TESTING}/pod_setup.sh
CONTAINERS+=( "${POD_NAME}-func" )

podman build -f ${TESTING}/functional.containerfile --tag functional "${BRANCH}"
podman run ${POD} --name="${POD_NAME}-func" localhost/functional
