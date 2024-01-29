import {createSlice, original} from "@reduxjs/toolkit";
import {CPT_INITIAL_DATA} from "./InitialData";

const jobsSlice = createSlice({
    initialState: {
        ...CPT_INITIAL_DATA,
    },
    name: 'ocpES',
    reducers: {
        getRhoaiNotebooksPerfJobsData: (state, action) => {
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
            state.jobTypes = ["All", ...action.payload.jobTypes]
            state.rehearses = ["All", ...action.payload.rehearses]
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  getRhoaiNotebooksPerfSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateRhoaiNotebooksPerfDataFilter: (state, action) => {
            const {ciSystem, platform, benchmark, version, workerCount, networkType, jobType, isRehearse} = action.payload
            state.selectedBenchmark = benchmark
            state.selectedVersion = version
            state.selectedPlatform = platform
            state.selectedNetworkType = networkType
            state.selectedWorkerCount = workerCount
            state.selectedCiSystem = ciSystem
            state.selectedJobType = jobType
            state.selectedRehearse = isRehearse
            state.data = getRhoaiNotebooksPerfUpdatedData(original(state.copyData), platform, benchmark, version, workerCount, networkType, ciSystem, jobType, isRehearse)
            Object.assign(state,  getRhoaiNotebooksPerfSummary(state.data))
        },
        updateRhoaiNotebooksPerfMetaData: (state, action) => {
            state.data = getRhoaiNotebooksPerfUpdatedData(action.payload.data, state.selectedPlatform, state.selectedBenchmark,
                state.selectedVersion, state.selectedWorkerCount, state.selectedNetworkType, state.selectedCiSystem,
                state.selectedJobType, state.selectedRehearse)
            Object.assign(state,  getRhoaiNotebooksPerfSummary(state.data))
        },
        setWaitForRhoaiNotebooksPerfUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorRhoaiNotebooksPerfCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})

const equalIgnoreCase = (value1 , value2, ...args) => {
    if(value1 && value2){
        let response = value1.toString().toUpperCase() === value2.toString().toUpperCase()
        args.forEach(item => response = item.toString().toUpperCase() === value1.toString().toUpperCase() && response)
        return response
    }
    return value1 === value2;
}

const getFilteredData = (data, selectedValue, keyValue) => {
    return data.filter(item => equalIgnoreCase(item[keyValue], selectedValue) || equalIgnoreCase(selectedValue, 'all') )
}

const getRhoaiNotebooksPerfUpdatedData = (data, platform, benchmark, version, workerCount, networkType, ciSystem, jobType, isRehearse) => {
    const filterValues = {
        "platform": platform, "benchmark": benchmark,
        "shortVersion": version, "workerNodesCount": workerCount,
        "networkType": networkType, "ciSystem": ciSystem,
        "jobType": jobType, "isRehearse": isRehearse,
    }
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues))
        filteredData = getFilteredData(filteredData, value, keyName)

    return filteredData
}

const getRhoaiNotebooksPerfSummary = (api_data) => {
    let success = 0;
    let failure = 0;
    let others = 0;
    let duration = 0;
    api_data.forEach(item => {
        if(item.jobStatus.toLowerCase() === "success") success++
        else if(item.jobStatus.toLowerCase() === "failure") failure++;
        else others++;
        duration += parseInt(item.jobDuration) ? parseInt(item.jobDuration) : 0;
    })
    const total = success + failure + others
    return {success, failure, others, total, duration}
}


export const {
    getRhoaiNotebooksPerfJobsData,
    updateRhoaiNotebooksPerfDataFilter,
    updateRhoaiNotebooksPerfMetaData,
    setWaitForRhoaiNotebooksPerfUpdate,
    errorRhoaiNotebooksPerfCall,
} = jobsSlice.actions
export default jobsSlice.reducer
