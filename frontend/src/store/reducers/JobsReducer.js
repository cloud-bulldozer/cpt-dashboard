
import {createSlice, original} from "@reduxjs/toolkit";
import {INITIAL_DATA} from "./InitialData";


const equalIgnoreCase = (value1 , value2, ...args) => {
    if(value1 && value2){
        let response = value1.toString().toUpperCase() === value2.toString().toUpperCase()
        args.forEach(item => response = item.toString().toUpperCase() === value1.toString().toUpperCase() && response)
        return response
    }
    return false

}


const getPlatformData = (platform, data) => {
    return data.filter(item => equalIgnoreCase(item.platform, platform) || equalIgnoreCase(platform, 'all') )
}

const getBenchmarkData = (benchmark, data) => {
    return data.filter(item => equalIgnoreCase(item.benchmark, benchmark) || equalIgnoreCase(benchmark, 'all') )
}

const getVersionsData = (version, data) => {
    return data.filter(item => equalIgnoreCase(item.shortVersion, version) || equalIgnoreCase(version, 'all') )
}

const getWorkersData = (workerCount, data) => {
    return data.filter(item => equalIgnoreCase(item.workerNodesCount, workerCount) || equalIgnoreCase(workerCount, 'all') )
}

const getNetworkTypesData = (networkType, data) => {
    return data.filter(item => equalIgnoreCase(item.networkType, networkType) || equalIgnoreCase(networkType, 'all') )
}

const getCiSystemData = (ciSystem, data) => {
    return data.filter(item => equalIgnoreCase(item.ciSystem, ciSystem) || equalIgnoreCase(ciSystem, 'all') )
}

const GetUpdatedData = (data, platform, benchmark, version, workerCount, networkType, ciSystem) => {
    const ciSystemData = getCiSystemData(ciSystem, data)
    const platformData = getPlatformData(platform, ciSystemData)
    const benchmarkData = getBenchmarkData(benchmark, platformData)
    const versionData = getVersionsData(version, benchmarkData)
    const workerData = getWorkersData(workerCount, versionData)
    return getNetworkTypesData(networkType, workerData)
}

const GetSummary = (api_data) => {
    let success = 0;
    let failure = 0;
    let others = 0;
    api_data.forEach(item => {
        if(item.jobStatus.toLowerCase() === "success") success++
        else if(item.jobStatus.toLowerCase() === "failure") failure++;
        else others++;
    })
    const total = success + failure + others
    return {success, failure, others, total}
}


const jobsSlice = createSlice({
    initialState: {
        ...INITIAL_DATA,
    },
    name: 'jenkins',
    reducers: {
        getJobsData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.benchmarks = ["All", ...action.payload.benchmarks]
            state.versions = ["All", ...action.payload.versions]
            state.waitForUpdate = action.payload.waitForUpdate
            state.platforms = ["All", ...action.payload.platforms]
            state.workers = ["All", ...action.payload.workers]
            state.networkTypes = ["All", ...action.payload.networkTypes]
            state.ciSystems = ["All", ...action.payload.ciSystems]
            state.updatedTime = action.payload.updatedTime
            state.error = null
            const {success, failure, others, total} = GetSummary(state.data)
            state.success = success
            state.failure = failure
            state.others = others
            state.total = total
        },
        updateDataFilter: (state, action) => {
            const {ciSystem, platform, benchmark, version, workerCount, networkType} = action.payload
            state.selectedBenchmark = benchmark
            state.selectedVersion = version
            state.selectedPlatform = platform
            state.selectedNetworkType = networkType
            state.selectedWorkerCount = workerCount
            state.selectedCiSystem = ciSystem
            state.data = GetUpdatedData(original(state.copyData), platform, benchmark, version, workerCount, networkType, ciSystem)
             const {success, failure, others, total} = GetSummary(state.data)
            state.success = success
            state.failure = failure
            state.others = others
            state.total = total
        },
        updateMetaData: (state, action) => {
            state.data = GetUpdatedData(action.payload.data, state.selectedPlatform, state.selectedBenchmark,
                state.selectedVersion, state.selectedWorkerCount, state.selectedNetworkType, state.selectedCiSystem)
            const {success, failure, others, total} = GetSummary(state.data)
            state.success = success
            state.failure = failure
            state.others = others
            state.total = total
        },
        setWaitForUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})
export const {getJobsData, updateDataFilter, setWaitForUpdate, updateMetaData, errorCall} = jobsSlice.actions
export default jobsSlice.reducer
