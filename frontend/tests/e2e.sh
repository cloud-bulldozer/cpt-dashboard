#!/bin/bash
if [ ${DEBUG} ]; then set -ex ;fi

BRANCH="$(git rev-parse --show-toplevel)"
TESTING="${BRANCH}/testing"
FRONTEND="${BRANCH}/frontend"

. ${TESTING}/pod_setup.sh
CYPRESS="${POD_NAME}-cypress"
CONTAINERS+=( "${CYPRESS}" )

podman build -f ${FRONTEND}/e2e_frontend.containerfile --tag cypress "${FRONTEND}"

mkdir -p "${FRONTEND}/coverage"

 
podman run ${POD} \
    -v "${FRONTEND}/coverage:/usr/src/cpt-dashboard/coverage" \
    --name="${CYPRESS}" \
    localhost/cypress

# TODO: no screenshots to upload until e2e tests are remediated
# podman cp ${CYPRESS}:/usr/src/cpt-dashboard/cypress/screenshots ${FRONTEND}/cypress/screenshots
