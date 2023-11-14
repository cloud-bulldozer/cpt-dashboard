

export const getUrl = () => {
    const {hostname, protocol} = window.location
    return (hostname === "localhost") ? "http://localhost:8000":`${protocol}//${hostname}`
}

export const BASE_URL = getUrl()
export const OCP_JOBS_API_V1 = "/api/ocp/v1/jobs"

export const OCP_GRAPH_API_V1 = "/api/ocp/v1/graph"
