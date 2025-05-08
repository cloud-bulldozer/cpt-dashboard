#!/bin/bash
set -ex

cleanup () {
    set +e
    echo "Cleaning up..."
    podman compose down
}

podman compose build
podman compose up --detach
# watch e2e tests for successful completion
podman compose logs --follow e2e-frontend
