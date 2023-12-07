import {createSlice, original} from "@reduxjs/toolkit";
import {CPT_INITIAL_DATA} from "./InitialData";
import { getCPTUpdatedData, getCPTSummary } from './Utils';


const jobsSlice = createSlice({
    initialState: {
        ...CPT_INITIAL_DATA,
    },
    name: 'cptES',
    reducers: {
        getCPTJobsData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.testNames = ["All", ...action.payload.testNames]
            state.products = ["All", ...action.payload.products]
            state.ciSystems = ["All", ...action.payload.ciSystems]
            state.jobStatuses = ["All", ...action.payload.jobStatuses]
            state.releaseStreams = ["All", ...action.payload.releaseStreams]
            state.waitForUpdate = action.payload.waitForUpdate
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  getCPTSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateCPTDataFilter: (state, action) => {
            const {ciSystem, testName, product, jobStatus, releaseStream} = action.payload
            state.selectedTestName = testName
            state.selectedProduct = product
            state.selectedCiSystem = ciSystem
            state.selectedJobStatus = jobStatus
            state.selectedReleaseStream = releaseStream
            state.data = getCPTUpdatedData(original(state.copyData), testName, product, ciSystem, jobStatus, releaseStream)
            Object.assign(state,  getCPTSummary(state.data))
        },
        updateCPTMetaData: (state, action) => {
            state.data = getCPTUpdatedData(action.payload.data, state.selectedTestName, state.selectedProduct,
                state.selectedCiSystem, state.selectedJobStatus, state.selectedReleaseStream)
            Object.assign(state,  getCPTSummary(state.data))
        },
        setWaitForCPTUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorCPTCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})
export const {
    getCPTJobsData,
    updateCPTDataFilter,
    updateCPTMetaData,
    setWaitForCPTUpdate,
    errorCPTCall,
} = jobsSlice.actions
export default jobsSlice.reducer
