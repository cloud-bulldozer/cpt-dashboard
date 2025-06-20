#!/bin/bash
set -ex # Fail on error
BRANCH=$(git rev-parse --show-toplevel)
TESTING=${BRANCH}/testing
COMPONENT=${COMPONENT:-ocp}

OSPORT=${OPENSEARCH_PORT:-9200}
NAME=${OPENSEARCH_NAME:-opensearch-${COMPONENT}}
OPENSEARCH_YML=${OPENSEARCH_YML:-${TESTING}/opensearch.yml}

if [[ -n "${POD_NAME}" ]] ;then
    echo "Running in POD ${POD_NAME}"
    POD="--pod ${POD_NAME}"
    NAME="${POD_NAME}-${NAME}"
    PORTS=
else
    POD=""
    PORTS="-p ${OSPORT}:${OSPORT}"
fi

if [ "${OSPORT}" != "9200" ] ;then
    PORTENV="-e http.port=${OSPORT}"
else
    PORTENV=
fi

podman run -d ${POD} --name "${NAME}" \
    -v "${OPENSEARCH_YML}":/usr/share/opensearch/config/opensearch.yml:z \
    ${PORTS} \
    -e "discovery.type=single-node" -e "DISABLE_INSTALL_DEMO_CONFIG=true" \
    -e "DISABLE_SECURITY_PLUGIN=true" ${PORTENV} \
    docker.io/opensearchproject/opensearch:latest
echo "Unpacking snapshot inside container"
podman cp "${TESTING}"/${COMPONENT}/snapshot.tar.gz "${NAME}":/var/tmp/snapshot.tar.gz
podman exec "${NAME}" bash -c 'cd /var/tmp ; tar xfz snapshot.tar.gz ; rm snapshot.tar.gz'
echo "Done"
