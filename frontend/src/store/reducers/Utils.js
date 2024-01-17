const equalIgnoreCase = (value1 , value2, ...args) => {
    if(value1 && value2){
        let response = value1.toString().toUpperCase() === value2.toString().toUpperCase()
        args.forEach(item => response = item.toString().toUpperCase() === value1.toString().toUpperCase() && response)
        return response
    }
    return value1 === value2;
}

const getFilteredData = (data, selectedValue, keyValue) => {
    return data.filter(item => equalIgnoreCase(item[keyValue], selectedValue) || equalIgnoreCase(selectedValue, 'all') )
}

const getCPTUpdatedData = (data, testName, product, ciSystem, jobStatus, releaseStream) => {
    const filterValues = {
        "testName": testName, "product": product,
        "ciSystem": ciSystem, "jobStatus": jobStatus,
        "releaseStream": releaseStream,
    }
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues))
        filteredData = getFilteredData(filteredData, value, keyName)

    return filteredData
}

const getOCPUpdatedData = (data, platform, benchmark, version, workerCount, networkType, ciSystem, jobType, isRehearse,
                            ipsec, fips, encrypted, encryptionType, publish, computeArch, controlPlaneArch) => {
    const filterValues = {
        "platform": platform, "benchmark": benchmark,
        "shortVersion": version, "workerNodesCount": workerCount,
        "networkType": networkType, "ciSystem": ciSystem,
        "jobType": jobType, "isRehearse": isRehearse,
        "ipsec": ipsec, "fips": fips, "encrypted": encrypted,
        "encryptionType": encryptionType, "publish": publish,
        "computeArch": computeArch, "controlPlaneArch": controlPlaneArch,
    }
    let filteredData = data
    for (let [keyName, value] of Object.entries(filterValues))
        filteredData = getFilteredData(filteredData, value, keyName)

    return filteredData
}

const getCPTSummary = (api_data) => {
    let success = 0;
    let failure = 0;
    let others = 0;
    api_data.forEach(item => {
        if(item.jobStatus.toLowerCase() === "success") success++
        else if(item.jobStatus.toLowerCase() === "failure") failure++;
        else others++;
    })
    const total = success + failure + others
    return {success, failure, others, total}
}

const getOCPSummary = (api_data) => {
    let success = 0;
    let failure = 0;
    let others = 0;
    let duration = 0;
    api_data.forEach(item => {
        if(item.jobStatus.toLowerCase() === "success") success++
        else if(item.jobStatus.toLowerCase() === "failure") failure++;
        else others++;
        duration += parseInt(item.jobDuration) ? parseInt(item.jobDuration) : 0;
    })
    const total = success + failure + others
    return {success, failure, others, total, duration}
}


export { getCPTUpdatedData, getOCPUpdatedData, getCPTSummary, getOCPSummary };