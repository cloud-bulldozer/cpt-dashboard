
import {BASE_URL, OCP_GRAPH_API_V1, OCP_JOBS_API_V1, CPT_JOBS_API_V1, QUAY_JOBS_API_V1, QUAY_GRAPH_API_V1, TELCO_JOBS_API_V1, TELCO_GRAPH_API_V1} from "../Shared";
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
import {
    errorQuayCall,
    getQuayJobsData,
    setWaitForQuayUpdate,
    updateQuayMetaData
} from "../reducers/QuayJobsReducer";
import {
    errorTelcoCall,
    getTelcoJobsData,
    setWaitForTelcoUpdate,
    updateTelcoMetaData
} from "../reducers/TelcoJobsReducer";
import {getUuidResults, setGraphError} from "../reducers/GraphReducer";
import {getQuayUuidResults, setQuayGraphError} from "../reducers/QuayGraphReducer";
import {getTelcoUuidResults, setTelcoGraphError} from "../reducers/TelcoGraphReducer";

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

export const fetchQuayGraphData =  (uuid) => async dispatch =>{
    try {
        let buildUrl = `${BASE_URL}${QUAY_GRAPH_API_V1}/${uuid}`
        const api_data = await fetchAPI(buildUrl)
        if(api_data) dispatch(getQuayUuidResults({ [uuid]: api_data }))
    }
    catch (error){
        if (axios.isAxiosError(error)) {
            console.error('Axios Error:', error);
            console.error('Request:', error.request);
            console.error('Response:', error.response);
        } else {
            console.error('Axios Error:', error);
            dispatch(setQuayGraphError({error: error.response.data.details}))
        }
    }
}

export const fetchTelcoGraphData =  (uuid, encryptedData) => async dispatch =>{
    try {
        let buildUrl = `${BASE_URL}${TELCO_GRAPH_API_V1}/${uuid}/${encryptedData}`
        const api_data = await fetchAPI(buildUrl)
        if(api_data) dispatch(getTelcoUuidResults({ [uuid]: api_data }))
    }
    catch (error){
        if (axios.isAxiosError(error)) {
            console.error('Axios Error:', error);
            console.error('Request:', error.request);
            console.error('Response:', error.response);
        } else {
            console.error('Axios Error:', error);
            dispatch(setTelcoGraphError({error: error.response.data.details}))
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
                const allIpsec = ["TRUE", "FALSE"]
                const allFips = ["TRUE", "FALSE"]
                const allEncrypted = ["TRUE", "FALSE"]
                const encryptionTypes = GetEncryptionTypes(results)
                const allPublish = GetPublish(results)
                const computeArchs = GetComputeArchs(results)
                const controlPlaneArchs = GetControlPlaneArchs(results)
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                await dispatch(getOCPJobsData({
                    data: results, benchmarks, versions, waitForUpdate: false, platforms, workers, networkTypes,
                    updatedTime, ciSystems, jobTypes, rehearses, allIpsec, allFips, allEncrypted, encryptionTypes,
                    allPublish, computeArchs, controlPlaneArchs, startDate: api_data.startDate, endDate: api_data.endDate
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

export const fetchQuayJobsData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${QUAY_JOBS_API_V1}`
    dispatch(setWaitForQuayUpdate({waitForUpdate:true}))
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
    }
    try{
        let api_data = await fetchAPI(buildUrl)
        dispatch(setWaitForQuayUpdate({waitForUpdate:false}))
        api_data = JSON.parse(api_data)
        if(api_data){
            const results = api_data.results
            if(results){
                const benchmarks = GetBenchmarks(results)
                const releaseStreams = GetReleaseStreams(results)
                const platforms = GetPlatforms(results)
                const workers = GetWorkers(results)
                const hitSizes = GetHitSizes(results)
                const concurrencies = GetConcurrencies(results)
                const imagePushPulls = GetImagePushPulls(results)
                const ciSystems = GetCiSystems(results)
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                await dispatch(getQuayJobsData({
                    data: results, benchmarks, releaseStreams, waitForUpdate: false, platforms, workers,
                    hitSizes, concurrencies, imagePushPulls, updatedTime, ciSystems, startDate: api_data.startDate, 
                    endDate: api_data.endDate
                }))
                await dispatch(updateQuayMetaData({data: results}))
            }
        }
    }
    catch (e) {
        const error = e
        if(error.response){
            await dispatch(errorQuayCall({error: error.response.data.error}))
            alert(error.response.data.error)
        }
        else{
            console.log(error)
        }
        dispatch(setWaitForQuayUpdate({waitForUpdate:false}))
    }
}

export const fetchTelcoJobsData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${TELCO_JOBS_API_V1}`
    dispatch(setWaitForTelcoUpdate({waitForUpdate:true}))
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
    }
    try{
        let api_data = await fetchAPI(buildUrl)
        dispatch(setWaitForTelcoUpdate({waitForUpdate:false}))
        api_data = JSON.parse(api_data)
        if(api_data){
            const results = api_data.results
            if(results){
                const benchmarks = GetBenchmarks(results)
                const versions = GetVersions(results)
                const releaseStreams = GetReleaseStreams(results)
                const ciSystems = GetCiSystems(results)
                const formals = GetFormals(results)
                const nodeNames = GetNodeNames(results)
                const cpus = GetCpus(results)
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                await dispatch(getTelcoJobsData({
                    data: results, benchmarks, versions, releaseStreams, waitForUpdate: false, formals, nodeNames, cpus,
                    updatedTime, ciSystems, startDate: api_data.startDate, endDate: api_data.endDate
                }))
                await dispatch(updateTelcoMetaData({data: results}))
            }
        }
    }
    catch (e) {
        const error = e
        if(error.response){
            await dispatch(errorTelcoCall({error: error.response.data.error}))
            alert(error.response.data.error)
        }
        else{
            console.log(error)
        }
        dispatch(setWaitForTelcoUpdate({waitForUpdate:false}))
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
    return Array.from(new Set(api_data.map(item => item.shortVersion).filter(shortVersion => shortVersion !== null && shortVersion !== "").map(shortVersion => shortVersion.toUpperCase().trim()))).sort(); 
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

const GetHitSizes = (api_data) => {
    return Array.from(new Set(api_data.map(item => parseInt(item.hitSize)))).sort((a, b) => a-b)
}

const GetConcurrencies = (api_data) => {
    return Array.from(new Set(api_data.map(item => parseInt(item.concurrency)))).sort((a, b) => a-b)
}

const GetImagePushPulls = (api_data) => {
    return Array.from(new Set(api_data.map(item => parseInt(item.imagePushPulls)))).sort((a, b) => a-b)
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
    return Array.from(new Set(api_data.map(item => item.releaseStream).filter(releaseStream => releaseStream !== null && releaseStream !== "").map(releaseStream => releaseStream.toUpperCase().trim()))).sort(); 
}

const GetFormals = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.formal).filter(formal => formal !== null && formal !== "").map(formal => formal.toUpperCase().trim()))).sort(); 
}

const GetNodeNames = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.nodeName).filter(nodeName => nodeName !== null && nodeName !== "").map(nodeName => nodeName.toUpperCase().trim()))).sort(); 
}

const GetCpus = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.cpu).filter(cpu => cpu !== null && cpu !== "").map(cpu => cpu.toUpperCase().trim()))).sort(); 
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

const GetEncryptionTypes = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.encryptionType.toUpperCase().trim()))).sort()
}

const GetPublish = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.publish.toUpperCase().trim()))).sort()
}

const GetComputeArchs = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.computeArch.toUpperCase().trim()))).sort()
}

const GetControlPlaneArchs = (api_data) => {
    return Array.from(new Set(api_data.map(item => item.controlPlaneArch.toUpperCase().trim()))).sort()
}