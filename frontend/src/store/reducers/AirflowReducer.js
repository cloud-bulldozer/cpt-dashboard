import {createSlice} from "@reduxjs/toolkit";
import {INITIAL_DATA} from "./InitialData";


const airflowSlice = createSlice({
    initialState: {
        ...INITIAL_DATA,
        system: "AirFlow"
    },
    name: 'airflow',
    reducers: {
        getAirflowData: (state, action) => {
            state.initialState = false
            state.success = action.payload.success
            state.failure = action.payload.failure
            state.total = action.payload.total
            state.response = action.payload.response
        }
    }
})
export const {getAirflowData} = airflowSlice.actions
export default airflowSlice.reducer
