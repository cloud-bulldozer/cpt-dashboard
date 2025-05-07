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



function run_pod_opensearch() {
    name=$1
    pod_name=$2
    osearch_cfg_path=$3

    podman rm -f ${pod_name}
    podman pod create --name=$pod_name --publish 9200:9200 --publish 9600:9600 --network=${POD_NAME}
    
    podman run -d --pod ${pod_name} --name "${name}" \
        -v "${osearch_cfg_path}":/usr/share/opensearch/config/opensearch.yml:z \
        -e "discovery.type=single-node" -e "DISABLE_INSTALL_DEMO_CONFIG=true" \
        -e "DISABLE_SECURITY_PLUGIN=true" \
        docker.io/opensearchproject/opensearch:latest
}

ocp="search-ocp"
ocp_pod="search-ocp-pod"

echo "running opensearch"
run_pod_opensearch ${ocp} ${ocp_pod} "${SETUP}"/functional/setup/ocp_opensearch.yml


podman cp ${SETUP}/fixtures/search_db_snapshots/snapshot.tar.gz ${ocp}:/var/tmp/snapshot.tar.gz
echo "Unpacking snapshot inside container"
podman exec "${ocp}" bash -c 'cd /var/tmp ; tar xfz snapshot.tar.gz'
echo "Done"

