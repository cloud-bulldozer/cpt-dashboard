import ocpJobsReducer from "./OCPJobsReducer";
import cptJobsReducer from "./CPTJobsReducer";
import quayJobsReducer from "./QuayJobsReducer";
import graphReducer from "./GraphReducer";
import quayGraphReducer from "./QuayGraphReducer";
import rhoaiNotebooksPerformanceJobsReducer from "./RHOAIJobsReducer";

export const rootReducer = {
    'ocpJobs': ocpJobsReducer,
    'cptJobs': cptJobsReducer,
    'quayJobs': quayJobsReducer,
    'graph': graphReducer,
    'quayGraph': quayGraphReducer,
    'rhoaiNotebooksPerformanceJobs': rhoaiNotebooksPerformanceJobsReducer,
}
