import ocpJobsReducer from "./OCPJobsReducer";
import cptJobsReducer from "./CPTJobsReducer";
import graphReducer from "./GraphReducer";


export const rootReducer = {
    'ocpJobs': ocpJobsReducer,
    'cptJobs': cptJobsReducer,
    'graph': graphReducer
}
