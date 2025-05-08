#!/bin/bash
set -ex # Fail on error
BRANCH=$(git rev-parse --show-toplevel)
SETUP=${BRANCH}/backend/tests


if [[ -n "${POD_NAME}" ]] ;then
    echo "Running in POD ${POD_NAME}"
    POD="--pod ${POD_NAME}"
    PORTS=
    NAME="${POD_NAME}-opensearch"
else
    POD=""
    PORTS="-p 9200:9200 -p 9600:9600"
    NAME="opensearch"
fi

podman rm -f ${NAME}

podman run -d ${POD} --name "${NAME}" \
    -v "${SETUP}"/functional/setup/ocp_opensearch.yml:/usr/share/opensearch/config/opensearch.yml:z \
    ${PORTS} \
    -e "discovery.type=single-node" -e "DISABLE_INSTALL_DEMO_CONFIG=true" \
    -e "DISABLE_SECURITY_PLUGIN=true" \
    --pull=always \
    docker.io/opensearchproject/opensearch:latest
podman cp ${SETUP}/fixtures/search_db_snapshots/snapshot.tar.gz ${NAME}:/var/tmp/snapshot.tar.gz
echo "Unpacking snapshot inside container"
podman exec "${NAME}" bash -c 'cd /var/tmp ; tar xfz snapshot.tar.gz'
echo "Done"
