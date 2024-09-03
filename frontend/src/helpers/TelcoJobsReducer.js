import {createSlice, original} from "@reduxjs/toolkit";
import {TELCO_INITIAL_DATA} from "./InitialData";
import { getTelcoUpdatedData, getTelcoSummary } from './Utils';

const jobsSlice = createSlice({
    initialState: {
        ...TELCO_INITIAL_DATA,
    },
    name: 'telcoSplunk',
    reducers: {
        getTelcoJobsData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.benchmarks = ["All", ...action.payload.benchmarks]
            state.versions = ["All", ...action.payload.versions]
            state.releaseStreams = ["All", ...action.payload.releaseStreams]
            state.ciSystems = ["All", ...action.payload.ciSystems]
            state.formals = ["All", ...action.payload.formals]
            state.nodeNames = ["All", ...action.payload.nodeNames]
            state.cpus = ["All", ...action.payload.cpus]
            state.waitForUpdate = action.payload.waitForUpdate
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  getTelcoSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateTelcoDataFilter: (state, action) => {
            const {ciSystem, benchmark, version, releaseStream, formal, nodeName, cpu} = action.payload
            state.selectedBenchmark = benchmark
            state.selectedVersion = version
            state.selectedReleaseStream = releaseStream
            state.selectedCiSystem = ciSystem
            state.selectedFormal = formal
            state.selectedNodeName = nodeName
            state.selectedCpu = cpu
            state.data = getTelcoUpdatedData(original(state.copyData), benchmark, version, releaseStream, ciSystem, formal, nodeName, cpu)
            Object.assign(state,  getTelcoSummary(state.data))
        },
        updateTelcoMetaData: (state, action) => {
            state.data = getTelcoUpdatedData(action.payload.data, state.selectedBenchmark, state.selectedVersion, state.selectedReleaseStream, 
                state.selectedCiSystem, state.selectedFormal, state.selectedNodeName, state.selectedCpu)
            Object.assign(state,  getTelcoSummary(state.data))
        },
        setWaitForTelcoUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorTelcoCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})
export const {
    getTelcoJobsData,
    updateTelcoDataFilter,
    updateTelcoMetaData,
    setWaitForTelcoUpdate,
    errorTelcoCall,
} = jobsSlice.actions
export default jobsSlice.reducer
