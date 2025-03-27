#!/bin/bash
set -ex # Fail on error
BRANCH=$(git rev-parse --show-toplevel)
SETUP=${BRANCH}/backend/tests/

if [[ -n "${POD_NAME}" ]] ;then
    echo "Running in POD ${POD_NAME}"
    POD="--pod ${POD_NAME}"
    PORTS=
    NAME="${POD_NAME}-opensearch"
else
    POD=""
    PORTS="-p 9201:9200 -p 9601:9600"
    NAME="opensearch"
fi

podman run -d ${POD} --name "${NAME}" \
    -v "${SETUP}"/functional/setup/opensearch.yml:/usr/share/opensearch/config/opensearch.yml:z \
    -v "${SETUP}"/fixtures/search_db_snapshots/ocp.tar.gz:/var/tmp/snapshot.tar.gz:z \
    ${PORTS} \
    -e "discovery.type=single-node" -e "DISABLE_INSTALL_DEMO_CONFIG=true" \
    -e "DISABLE_SECURITY_PLUGIN=true" \
    docker.io/opensearchproject/opensearch:latest
echo "Unpacking snapshot inside container"
podman exec "${NAME}" bash -c 'cd /var/tmp ; tar xfz snapshot.tar.gz'
echo "Done"
