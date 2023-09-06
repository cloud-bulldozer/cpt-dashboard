import {createSlice} from "@reduxjs/toolkit";
import {INITIAL_DATA} from "./InitialData";


const jenkinsSlice = createSlice({
    initialState: {
        ...INITIAL_DATA,
        system: "Jenkins"
    },
    name: 'jenkins',
    reducers: {
        getJenkinsData: (state, action) => {
            state.initialState = false
            state.success = action.payload.success
            state.failure = action.payload.failure
            state.total = action.payload.total
            state.response = action.payload.response
        }
    }
})
export const {getJenkinsData} = jenkinsSlice.actions
export default jenkinsSlice.reducer
