import {createSlice} from "@reduxjs/toolkit";
import {QUAY_GRAPH_INITIAL_DATA} from "./InitialData";


const quayGraphReducer = createSlice({
    initialState: {
        ...QUAY_GRAPH_INITIAL_DATA,
    },
    name: 'quayGraph',
    reducers: {
        getQuayUuidResults: (state, action) => {
            Object.assign(state.uuid_results, action.payload)
        },
        setQuayGraphError: (state, action) => {
            Object.assign(state.graphError, action.payload.error)
        }
    }
})

export const {
    getQuayUuidResults,
    setQuayGraphError
} = quayGraphReducer.actions
export default quayGraphReducer.reducer
