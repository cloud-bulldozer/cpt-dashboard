
import {BASE_URL, OCP_GRAPH_API_V1, OCP_JOBS_API_V1, CPT_JOBS_API_V1} from "../Shared";
import axios from "axios";
import {
    errorOCPCall,
    getOCPJobsData,
    setWaitForOCPUpdate,
    updateOCPMetaData
} from "../reducers/OCPJobsReducer";
import {
    errorCPTCall,
    getCPTJobsData,
    setWaitForCPTUpdate,
    updateCPTMetaData
} from "../reducers/CPTJobsReducer";
import {getUuidResults, setGraphError} from "../reducers/GraphReducer";

export const fetchAPI = async (url, requestOptions = {}) => {
    const response = await axios(url, requestOptions)
    return response.data
}

export const fetchGraphData =  (uuid) => async dispatch =>{
    try {
        let buildUrl = `${BASE_URL}${OCP_GRAPH_API_V1}/${uuid}`
        const api_data = await fetchAPI(buildUrl)
        if(api_data) dispatch(getUuidResults({ [uuid]: api_data }))
    }
    catch (error){
        if (axios.isAxiosError(error)) {
            console.error('Axios Error:', error);
            console.error('Request:', error.request);
            console.error('Response:', error.response);
        } else {
            console.error('Axios Error:', error);
            dispatch(setGraphError({error: error.response.data.details}))
        }
    }
}

export const fetchOCPJobsData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${OCP_JOBS_API_V1}`
    dispatch(setWaitForOCPUpdate({waitForUpdate:true}))
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
    }
    try{
        let api_data = await fetchAPI(buildUrl)
        dispatch(setWaitForOCPUpdate({waitForUpdate:false}))
        api_data = JSON.parse(api_data)
        if(api_data){
            const results = api_data.results
            if(results){
                const benchmarks = GetBenchmarks(results)
                const versions = GetVersions(results)
                const platforms = GetPlatforms(results)
                const workers = GetWorkers(results)
                const networkTypes = GetNetworkTypes(results)
                const ciSystems = GetCiSystems(results)
                const jobTypes = GetJobType(results)
                const rehearses = ["TRUE", "FALSE"]
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                await dispatch(getOCPJobsData({
                    data: results, benchmarks, versions, waitForUpdate: false, platforms, workers, networkTypes,
                    updatedTime, ciSystems, jobTypes, rehearses, startDate: api_data.startDate, endDate: api_data.endDate
                }))
                await dispatch(updateOCPMetaData({data: results}))
            }
        }
    }
    catch (e) {
        const error = e
        if(error.response){
            await dispatch(errorOCPCall({error: error.response.data.error}))
            alert(error.response.data.error)
        }
        else{
            console.log(error)
        }
        dispatch(setWaitForOCPUpdate({waitForUpdate:false}))
    }
}

export const fetchCPTJobsData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${CPT_JOBS_API_V1}`
    dispatch(setWaitForCPTUpdate({waitForUpdate:true}))
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
    }
    try{
        let api_data = await fetchAPI(buildUrl)
        dispatch(setWaitForCPTUpdate({waitForUpdate:false}))
        api_data = JSON.parse(api_data)
        if(api_data){
            const results = api_data.results
            if(results){
                const testNames = GetTestNames(results)
                const products = GetProducts(results)
                const ciSystems = GetCiSystems(results)
                const jobStatuses = GetStatuses(results)
                const releaseStreams = GetReleaseStreams(results)
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                await dispatch(getCPTJobsData({
                    data: results, testNames, products, waitForUpdate: false,
                    jobStatuses, releaseStreams, updatedTime, ciSystems, startDate: api_data.startDate, endDate: api_data.endDate
                }))
                await dispatch(updateCPTMetaData({data: results}))
            }
        }
    }
    catch (e) {
        const error = e
        if(error.response){
            await dispatch(errorCPTCall({error: error.response.data.error}))
            alert(error.response.data.error)
        }
        else{
            console.log(error)
        }
        dispatch(setWaitForCPTUpdate({waitForUpdate:false}))
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

const GetProducts = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.product.toUpperCase().trim()))).sort()
}

const GetStatuses = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.jobStatus.toUpperCase().trim()))).sort()
}

const GetReleaseStreams = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.releaseStream.toUpperCase().trim()))).sort()
}

const GetTestNames = (api_data) => {
    return Array.from(new Set(api_data.map(item => {
        if(item.testName === null) return ''
        else return item.testName.toLowerCase().trim()
    }))).sort()
}

const GetJobType = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.jobType.toUpperCase().trim()))).sort()
}