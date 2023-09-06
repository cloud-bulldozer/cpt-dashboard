import {createSlice} from "@reduxjs/toolkit";
import {INITIAL_DATA} from "./InitialData";


const prowCiSlice = createSlice({
    initialState: {
        ...INITIAL_DATA,
        system: "ProwCI"
    },
    name: 'prowci',
    reducers: {
        getProwCIData: (state, action) => {
            state.initialState = false
            state.success = action.payload.success
            state.failure = action.payload.failure
            state.total = action.payload.total
            state.response = action.payload.response
        }
    }
})
export const {getProwCIData} = prowCiSlice.actions
export default prowCiSlice.reducer
