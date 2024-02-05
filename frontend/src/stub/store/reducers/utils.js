import { getFilteredData } from '../../../store/reducers/Utils';


const getStubUpdatedData = (data, builtComponents) => {
    const filterValues = {}
    for (let [key, value] of Object.entries(builtComponents)) {
        filterValues[key] = value
    }
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues)){
        filteredData = getFilteredData(filteredData, value, keyName)
    }

    return filteredData
}


export { getStubUpdatedData };