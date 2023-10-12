

export const getUrl = () => {
    const {hostname, protocol} = window.location
    return (hostname === "localhost") ? "http://localhost:8000":`${protocol}//${hostname}`
}

export const BASE_URL = getUrl()
export const JOBS_API_V2 = "/api/v2/jobs"

export const GRAPH_API_V1 = "/api/v1/graph"
