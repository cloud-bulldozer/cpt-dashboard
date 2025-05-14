#!/bin/bash
set -ex

cleanup () {
    set +e
    echo "Cleaning up..."
    podman compose down
}

BRANCH="$(git rev-parse --show-toplevel)"
BACKEND="${BRANCH}/backend"
FRONTEND="${BRANCH}/frontend"
SETUP="${BACKEND}"/tests/functional/setup
CPT_CONFIG=${CPT_CONFIG:-"${SETUP}/funcconfig.toml"}

trap cleanup EXIT

# generate application version file
${BACKEND}/scripts/version.py       

# depends upon the e2e test's container name in the compose file
CYPRESS_POD="e2e-in-network"

podman compose --file ${BRANCH}/compose.yaml build
podman compose --file ${BRANCH}/compose.yaml --profile e2e-in-network up --detach
# watch e2e tests for successful completion
podman compose --file ${BRANCH}/compose.yaml logs --follow ${CYPRESS_POD}
podman cp ${CYPRESS_POD}:/usr/src/cpt-dashboard/cypress/screenshots ${FRONTEND}/cypress/screenshots
