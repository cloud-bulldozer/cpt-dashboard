import {createSlice} from "@reduxjs/toolkit";
import {TELCO_GRAPH_INITIAL_DATA} from "./InitialData";


const telcoGraphReducer = createSlice({
    initialState: {
        ...TELCO_GRAPH_INITIAL_DATA,
    },
    name: 'telcoGraph',
    reducers: {
        getTelcoUuidResults: (state, action) => {
            Object.assign(state.uuid_results, action.payload)
        },
        setTelcoGraphError: (state, action) => {
            Object.assign(state.graphError, action.payload.error)
        }
    }
})

export const {
    getTelcoUuidResults,
    setTelcoGraphError
} = telcoGraphReducer.actions
export default telcoGraphReducer.reducer