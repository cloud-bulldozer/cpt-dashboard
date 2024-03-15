import {createSlice, original} from "@reduxjs/toolkit";
import {STUB_INITIAL_DATA} from '../stub';
import { getStubUpdatedData } from './utils';


const jobsSlice = createSlice({
    initialState: {
        ...STUB_INITIAL_DATA,
    },
    name: 'stubData',
    reducers: {
        getStubData: (state, action) => {
            state.initialState = false
            state.copyData = action.payload.data
            state.data = action.payload.data
            state.updatedTime = action.payload.updatedTime
            state.error = null
            state.startDate = action.payload.startDate
            state.endDate = action.payload.endDate
            state.updatedTime = action.payload.updatedTime
            state.tableData = action.payload.tableData
            state.filtersData = action.payload.filtersData
        },
        updateStubDataFilter: (state, action) => {
            const { builtSidebarComponents } = action.payload
            if (builtSidebarComponents !== undefined) {
                for (let [key, value] of Object.entries(builtSidebarComponents)) {
                    state.selectedValues[key] = value
                }
                state.data = getStubUpdatedData(original(state.copyData), builtSidebarComponents)
            }
        },
        updateStubMetaData: (state, action) => {
            state.data = getStubUpdatedData(action.payload.data, state.selectedValues)
        },
        setWaitForStubUpdate: (state, action) => {
            state.waitForUpdate = action.payload.waitForUpdate
        },
        errorStubCall: (state, action) => {
            state.error = action.payload.error
        }
    }
})
export const {
    getStubData,
    updateStubDataFilter,
    updateStubMetaData,
    setWaitForStubUpdate,
    errorStubCall,
} = jobsSlice.actions
export default jobsSlice.reducer
