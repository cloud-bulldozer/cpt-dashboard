import {createSlice, original} from "@reduxjs/toolkit";
import {QUAY_INITIAL_DATA} from "./InitialData";
import { getQuayUpdatedData, getQuaySummary } from './Utils';

const jobsSlice = createSlice({
    initialState: {
        ...QUAY_INITIAL_DATA,
    },
    name: 'quayES',
    reducers: {
        getQuayJobsData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.benchmarks = ["All", ...action.payload.benchmarks]
            state.releaseStreams = ["All", ...action.payload.releaseStreams]
            state.waitForUpdate = action.payload.waitForUpdate
            state.platforms = ["All", ...action.payload.platforms]
            state.workers = ["All", ...action.payload.workers]
            state.hitSizes = ["All", ...action.payload.hitSizes]
            state.concurrencies = ["All", ...action.payload.concurrencies]
            state.imagePushPulls = ["All", ...action.payload.imagePushPulls]
            state.ciSystems = ["All", ...action.payload.ciSystems]
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  getQuaySummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateQuayDataFilter: (state, action) => {
            const {ciSystem, platform, benchmark, releaseStream, workerCount, hitSize, concurrency, imagePushPulls} = action.payload
            state.selectedBenchmark = benchmark
            state.selectedReleaseStream = releaseStream
            state.selectedPlatform = platform
            state.selectedWorkerCount = workerCount
            state.selectedCiSystem = ciSystem
            state.selectedHitSize = hitSize
            state.selectedConcurrency = concurrency
            state.selectedImagePushPulls = imagePushPulls
            state.data = getQuayUpdatedData(original(state.copyData), platform, benchmark, releaseStream, workerCount, ciSystem, hitSize, concurrency, imagePushPulls)
            Object.assign(state,  getQuaySummary(state.data))
        },
        updateQuayMetaData: (state, action) => {
            state.data = getQuayUpdatedData(action.payload.data, state.selectedPlatform, state.selectedBenchmark,
                state.selectedReleaseStream, state.selectedWorkerCount, state.selectedCiSystem, state.selectedHitSize,
                state.selectedConcurrency, state.selectedImagePushPulls)
            Object.assign(state,  getQuaySummary(state.data))
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
