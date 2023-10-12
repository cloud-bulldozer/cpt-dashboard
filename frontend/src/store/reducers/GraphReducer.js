import {createSlice} from "@reduxjs/toolkit";
import {GRAPH_INITIAL_DATA} from "./InitialData";


const graphReducer = createSlice({
    initialState: {
        ...GRAPH_INITIAL_DATA,
    },
    name: 'Graph',
    reducers: {
        getUuidResults: (state, action) => {
            Object.assign(state.uuid_results, action.payload)
        },
        setGraphError: (state, action) => {
            Object.assign(state.graphError, action.payload.error)
        }
    }
})

export const {
    getUuidResults,
    setGraphError
} = graphReducer.actions
export default graphReducer.reducer
