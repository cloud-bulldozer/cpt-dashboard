import ocpJobsReducer from "./OCPJobsReducer";
import cptJobsReducer from "./CPTJobsReducer";
import quayJobsReducer from "./QuayJobsReducer";
import telcoJobsReducer from "./TelcoJobsReducer";
import graphReducer from "./GraphReducer";
import quayGraphReducer from "./QuayGraphReducer";
import telcoGraphReducer from "./TelcoGraphReducer";


export const rootReducer = {
    'ocpJobs': ocpJobsReducer,
    'cptJobs': cptJobsReducer,
    'quayJobs': quayJobsReducer,
    'telcoJobs': telcoJobsReducer,
    'graph': graphReducer,
    'quayGraph': quayGraphReducer,
    'telcoGraph': telcoGraphReducer,
}
