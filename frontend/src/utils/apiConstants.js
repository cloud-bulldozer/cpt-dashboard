export const getUrl = () => {
  const { hostname, protocol } = window.location;
  return hostname === "localhost"
    ? "http://localhost:8000"
    : `${protocol}//${hostname}`;
};

export const BASE_URL = getUrl();

export const OCP_JOBS_API_V1 = "/api/v1/ocp/jobs";
export const OCP_GRAPH_API_V1 = "/api/v1/ocp/graph";
export const OCP_FILTERS_API_V1 = "/api/v1/ocp/filters";

export const CPT_JOBS_API_V1 = "/api/v1/cpt/jobs";
export const CPT_FILTERS_API_V1 = "/api/v1/cpt/filters";

export const QUAY_JOBS_API_V1 = "/api/v1/quay/jobs";
export const QUAY_GRAPH_API_V1 = "/api/v1/quay/graph";
export const QUAY_FILTERS_API_V1 = "/api/v1/quay/filters";

export const TELCO_JOBS_API_V1 = "/api/v1/telco/jobs";
export const TELCO_GRAPH_API_V1 = "/api/v1/telco/graph";
