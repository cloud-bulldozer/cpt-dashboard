import { getFilteredData } from '../../../store/reducers/Utils';


const getStubUpdatedData = (data) => {
    const filterValues = {}
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues)){
        filteredData = getFilteredData(filteredData, value, keyName)
    }

    return filteredData
}


export { getStubUpdatedData };