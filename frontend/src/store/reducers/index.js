import airflowReducer from "./AirflowReducer";
import prowCiReducer from "./ProwciReducer";
import jenkinsReducer from "./JenkinsReducer";


export const rootReducer = {
    'airflow': airflowReducer,
    'prowci': prowCiReducer,
    'jenkins': jenkinsReducer
}
