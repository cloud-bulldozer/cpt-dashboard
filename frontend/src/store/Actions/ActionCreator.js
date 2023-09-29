
import {BASE_URL, JOBS_API_V2} from "../Shared";
import axios from "axios";
import {errorCall, getJobsData, setWaitForUpdate, updateMetaData} from "../reducers/JobsReducer";


export const fetchAPI = async (url, requestOptions = {}) => {
    const response = await axios(url, requestOptions)
    return JSON.parse(response.data)
}


export const fetchJobsData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${JOBS_API_V2}`
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
        dispatch(setWaitForUpdate({waitForUpdate:true}))
    }
    try{
         const api_data = await fetchAPI(buildUrl)
        if(api_data){
            const results = api_data.results
            const benchmarks = GetBenchmarks(results)
            const versions = GetVersions(results)
            const platforms = GetPlatforms(results)
            const workers = GetWorkers(results)
            const networkTypes = GetNetworkTypes(results)
            const ciSystems = GetCiSystems(results)
            const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
            await dispatch(getJobsData({
                data: results, benchmarks, versions, waitForUpdate: false, platforms, workers, networkTypes,
                updatedTime, ciSystems, startDate: api_data.startDate, endDate: api_data.endDate
            }))
            await dispatch(updateMetaData({data: results}))
        }
    }
    catch (e) {
        const error = e
        if(error){
            await dispatch(errorCall({error: error.response.data.error}))
            dispatch(setWaitForUpdate({waitForUpdate:false}))
            alert(error.response.data.error)
        }
    }

}


const GetCiSystems = (api_data) => {
    return Array.from(new Set(api_data.map(item => {
        if(item.ciSystem === null) return ''
        else return item.ciSystem.toUpperCase().trim()
    }))).sort()
}

export const GetVersions = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.shortVersion.toLowerCase().trim()))).sort()
}

export const GetBenchmarks = (api_data) => {
    return Array.from(new Set(api_data.map(item => {
        if(item.benchmark === null) return ''
        else return item.benchmark.toLowerCase().trim()
    }))).sort()
}


const GetPlatforms = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.platform.toUpperCase().trim()))).sort()
}

const GetWorkers = (api_data) => {
    return Array.from(new Set(api_data.map(item => parseInt(item.workerNodesCount)))).sort((a, b) => a-b)
}

const GetNetworkTypes = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.networkType.toUpperCase().trim()))).sort()
}
