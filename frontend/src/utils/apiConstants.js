export const getUrl = () => {
  const { protocol, hostname, port } = window.location;

  // Try to support three environments. If we're running a development
  // environment on localhost, map to the API port. If we're running on
  // the product OpenShift environment with an API reverse proxy, we
  // won't see a port, and the API calls will be routed correctly without
  // a port. If we're running a "product" deployment outside of OpenShift
  // and without a routing reverse proxy, we'll see the origin port 3000
  // and route to the same protocol/host with port 8000.
  if (hostname === "localhost") {
    return "http://0.0.0.0:8000";
  } else if (port === "3000") {
    return `${protocol}//${hostname}:8000`;
  } else {
    return `${protocol}//${hostname}`;
  }
};

export const BASE_URL = getUrl();

export const OCP_JOBS_API_V1 = "/api/v1/ocp/jobs";
export const OCP_GRAPH_API_V1 = "/api/v1/ocp/graph";

export const CPT_JOBS_API_V1 = "/api/v1/cpt/jobs";

export const QUAY_JOBS_API_V1 = "/api/v1/quay/jobs";
export const QUAY_GRAPH_API_V1 = "/api/v1/quay/graph";

export const TELCO_JOBS_API_V1 = "/api/v1/telco/jobs";
export const TELCO_GRAPH_API_V1 = "/api/v1/telco/graph";

export const ILABS_JOBS_API_V1 = "/api/v1/ilab/runs";
export const ILAB_GRAPH_API_V1 = "/api/v1/ilab/runs/";
