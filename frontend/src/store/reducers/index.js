import jobsReducer from "./JobsReducer";
import graphReducer from "./GraphReducer";


export const rootReducer = {
    'jobs': jobsReducer,
    'graph': graphReducer
}
