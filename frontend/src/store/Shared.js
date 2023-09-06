

export const getUrl = () => {
    const {hostname, protocol} = window.location
    return (hostname === "localhost") ? "http://localhost:8000":`${protocol}//${protocol}`
}

export const BASE_URL = getUrl()

