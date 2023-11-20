import {createSlice, original} from "@reduxjs/toolkit";
import {CPT_INITIAL_DATA} from "./InitialData";


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

const GetUpdatedData = (data, testName, product, ciSystem, jobStatus) => {
    const filterValues = {
        "testName": testName, "product": product,
        "ciSystem": ciSystem, "jobStatus": jobStatus,
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
            state.waitForUpdate = action.payload.waitForUpdate
            state.updatedTime = action.payload.updatedTime
            state.error = null
            Object.assign(state,  GetSummary(state.data))
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
        },
        updateCPTDataFilter: (state, action) => {
            const {ciSystem, testName, product, jobStatus} = action.payload
            state.selectedTestName = testName
            state.selectedProduct = product
            state.selectedCiSystem = ciSystem
            state.selectedJobStatus = jobStatus
            state.data = GetUpdatedData(original(state.copyData), testName, product, ciSystem, jobStatus)
            Object.assign(state,  GetSummary(state.data))
        },
        updateCPTMetaData: (state, action) => {
            state.data = GetUpdatedData(action.payload.data, state.selectedTestName, state.selectedProduct,
                state.selectedCiSystem, state.selectedJobStatus)
            Object.assign(state,  GetSummary(state.data))
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
