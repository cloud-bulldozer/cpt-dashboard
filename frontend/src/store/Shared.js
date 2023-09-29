

export const getUrl = () => {
    var hostname = window.location.hostname
    if (hostname === "localhost") {
        var host = "http://localhost:8000";
    } else {
        var host = window.location.protocol + '//' + window.location.hostname;
    }
    return host
}

export const BASE_URL = getUrl()
export const JOBS_API_V2 = "/api/v2/jobs"

