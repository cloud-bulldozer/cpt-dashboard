import {getJenkinsData} from "../reducers/JenkinsReducer";
import {getAirflowData} from "../reducers/AirflowReducer";
import {getProwCIData} from "../reducers/ProwciReducer";
import {BASE_URL} from "../Shared";
import axios from "axios";


export const fetchAPI = async (url, requestOptions = {}) => {
    const response = await axios(url, requestOptions)
    return response.data
}


export const fetchJenkinsData = (ci_system) => async dispatch => {
    const buildUrl = `${BASE_URL}/api/jenkins`
    const api_data = await fetchAPI(buildUrl)
    if(api_data.response) {
        const {success, failure, total} = getAggregatedResults(api_data)
        await dispatch(getJenkinsData({success, failure, total, response: api_data.response}))
    }
}

export const fetchAirflowData = () => async dispatch => {
    const buildUrl = `${BASE_URL}/api/airflow`
    const api_data = await fetchAPI(buildUrl)
    if(api_data.response) {
        const {success, failure, total} = getAggregatedResults(api_data)
        dispatch(getAirflowData({success, failure, total, response: api_data.response}))
    }
}

export const fetchProwCIData = () => async dispatch => {
    const buildUrl = `${BASE_URL}/api/jobs`
    const api_data = await fetchAPI(buildUrl)
    if(api_data.response) {
        const {success, failure, total} = getAggregatedResults(api_data)
        dispatch(getProwCIData({success, failure, total, response: api_data.response}))
    }
}

export const getAggregatedResults = (api_data) => {
    const cloud_data = api_data.response
    let success =  0
    let failure = 0
    cloud_data.forEach(item1 => {
        item1.data.forEach(item2 => {
            item2.cloud_data.forEach(item3 => {
                item3.forEach(item4 => {
                    if(item4 !== null) {
                        if (item4 === 'success') success++;
                        else if (item4 === 'failure') failure++;
                    }
                })
            })
        })
    })
    return { success, failure, total: success + failure }
}
