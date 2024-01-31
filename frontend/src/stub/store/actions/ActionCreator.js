import {BASE_URL, STUB_JOBS_API_V1} from "../../../store/Shared";
import {
    getStubData,
    setWaitForStubUpdate,
    updateStubMetaData,
    errorStubCall
} from "../reducers/StubReducer";
import {fetchAPI} from "../../../store/Actions/ActionCreator"


export const fetchStubData = (startDate = '', endDate='') => async dispatch => {
    let buildUrl = `${BASE_URL}${STUB_JOBS_API_V1}`
    dispatch(setWaitForStubUpdate({waitForUpdate:true}))
    if(startDate !== '' && endDate !== '') {
        buildUrl += `?start_date=${startDate}&end_date=${endDate}`
    }
    try{
        let api_data = await fetchAPI(buildUrl)
        dispatch(setWaitForStubUpdate({waitForUpdate:false}))
        if(api_data){
            const results = api_data.results
            if(results){
                const updatedTime = new Date().toLocaleString().replace(', ', ' ').toString();
                const tableData = buildTableData(api_data.columns)
                const filtersData = buildFilters(api_data.filters, results)
                await dispatch(getStubData({
                    data: results, updatedTime, startDate: api_data.startDate, endDate: api_data.endDate,
                    tableData: tableData, filtersData: filtersData
                }))
                await dispatch(updateStubMetaData({data: results}))
            }
        }
    }
    catch (e) {
        const error = e
        if(error.response){
            await dispatch(errorStubCall({error: error.response.data.error}))
            alert(error.response.data.error)
        }
        else{
            console.log(error)
        }
        dispatch(setWaitForStubUpdate({waitForUpdate:false}))
    }
}


const buildTableData = (columns) => {
    let results = []
    for (const [key, value] of Object.entries(columns)) {
        let r = {name: value, value: key }
        results.push(r)
    }
    return results
}

const buildFilters = (filters, data) => {
    let results = []
    for (const [key, value] of Object.entries(filters)) {
        let items = ["All"]

        let values = Array.from(new Set(data.map(
                item => {
                    if(item[key] === null) return ''
                    else if (typeof(item[key]) === "number") return item[key]
                    else return item[key].toUpperCase().trim()
            }
            ))).sort();
        items.push(...values);

        let r = {name: key,
                 display: value,
                 items: items }
        results.push(r)
    }
    return results
}

