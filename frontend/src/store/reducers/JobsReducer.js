
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


const getFilteredData = (data, selectedValue, keyValue) => {
    return data.filter(item => equalIgnoreCase(item[keyValue], selectedValue) || equalIgnoreCase(selectedValue, 'all') )
}

const GetUpdatedData = (data, platform, benchmark, version, workerCount, networkType, ciSystem) => {
    const filterValues = {
        "platform": platform, "benchmark": benchmark,
        "shortVersion": version, "workerNodesCount": workerCount,
        "networkType": networkType, "ciSystem": ciSystem
    }
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues))
        filteredData = getFilteredData(filteredData, value, keyName)

    return filteredData
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
            Object.assign(state,  GetSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
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
            Object.assign(state,  GetSummary(state.data))
        },
        updateMetaData: (state, action) => {
            state.data = GetUpdatedData(action.payload.data, state.selectedPlatform, state.selectedBenchmark,
                state.selectedVersion, state.selectedWorkerCount, state.selectedNetworkType, state.selectedCiSystem)
            Object.assign(state,  GetSummary(state.data))
        },
        setWaitForUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorCall: (state, action) => {
            state.error = action.payload.error
        },
        getUuidResults: (state, action) => {
            Object.assign(state.uuid_results, action.payload.data)
        },
    }
})
export const {getJobsData, updateDataFilter, setWaitForUpdate, updateMetaData, errorCall} = jobsSlice.actions
export default jobsSlice.reducer
