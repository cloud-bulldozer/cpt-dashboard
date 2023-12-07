import {createSlice, original} from "@reduxjs/toolkit";
import {OCP_INITIAL_DATA} from "./InitialData";
import { getOCPUpdatedData, getOCPSummary } from './Utils';

const jobsSlice = createSlice({
    initialState: {
        ...OCP_INITIAL_DATA,
    },
    name: 'quayES',
    reducers: {
        getQuayJobsData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.benchmarks = ["All", ...action.payload.benchmarks]
            state.versions = ["All", ...action.payload.versions]
            state.waitForUpdate = action.payload.waitForUpdate
            state.platforms = ["All", ...action.payload.platforms]
            state.workers = ["All", ...action.payload.workers]
            state.ciSystems = ["All", ...action.payload.ciSystems]
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  getOCPSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateQuayDataFilter: (state, action) => {
            const {ciSystem, platform, benchmark, version, workerCount} = action.payload
            state.selectedBenchmark = benchmark
            state.selectedVersion = version
            state.selectedPlatform = platform
            state.selectedWorkerCount = workerCount
            state.selectedCiSystem = ciSystem
            state.data = getOCPUpdatedData(original(state.copyData), platform, benchmark, version, workerCount, 'all', ciSystem, 'all', 'all')
            Object.assign(state,  getOCPSummary(state.data))
        },
        updateQuayMetaData: (state, action) => {
            state.data = getOCPUpdatedData(action.payload.data, state.selectedPlatform, state.selectedBenchmark,
                state.selectedVersion, state.selectedWorkerCount, 'all', state.selectedCiSystem, 'all', 'all')
            Object.assign(state,  getOCPSummary(state.data))
        },
        setWaitForQuayUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorQuayCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})
export const {
    getQuayJobsData,
    updateQuayDataFilter,
    updateQuayMetaData,
    setWaitForQuayUpdate,
    errorQuayCall,
} = jobsSlice.actions
export default jobsSlice.reducer
