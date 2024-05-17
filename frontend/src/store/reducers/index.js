import ocpJobsReducer from "./OCPJobsReducer";
import cptJobsReducer from "./CPTJobsReducer";
import quayJobsReducer from "./QuayJobsReducer";
import telcoJobsReducer from "./TelcoJobsReducer";
import graphReducer from "./GraphReducer";
import quayGraphReducer from "./QuayGraphReducer";


export const rootReducer = {
    'ocpJobs': ocpJobsReducer,
    'cptJobs': cptJobsReducer,
    'quayJobs': quayJobsReducer,
    'telcoJobs': telcoJobsReducer,
    'graph': graphReducer,
    'quayGraph': quayGraphReducer,
}
