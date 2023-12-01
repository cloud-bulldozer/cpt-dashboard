import '../css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect, useState} from 'react';

import {HomeLayout} from "../templates/HomeLayout";
import {useDispatch, useSelector} from "react-redux";
import {useHistory, useLocation} from "react-router-dom";
import {updateOCPDataFilter} from "../../store/reducers/OCPJobsReducer";
import {fetchOCPJobsData} from "../../store/Actions/ActionCreator";
import {BenchmarkResults} from "./BenchmarkResults";


export function OCPHome() {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();
    const ocpJobs = useSelector(state => state.ocpJobs)

    const topHeadersData = [
      {loading: ocpJobs.waitForUpdate, title: 'No. Jobs', value: ocpJobs.total},
      {loading: ocpJobs.waitForUpdate, title: 'Success', value: ocpJobs.success},
      {loading: ocpJobs.waitForUpdate, title: 'Failure', value: ocpJobs.failure},
      {loading: ocpJobs.waitForUpdate, title: 'Others', value: ocpJobs.others},
      {loading: ocpJobs.waitForUpdate, title: 'Duration Running', value: ocpJobs.duration}
  ]

    const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || ocpJobs.selectedCiSystem)
    const [platform, setPlatform] = useState(searchParams.get("platform") || ocpJobs.selectedPlatform)
    const [benchmark, setBenchmark] = useState(searchParams.get("benchmark") || ocpJobs.selectedBenchmark)
    const [workerCount, setWorkerCount] = useState(searchParams.get("workerCount") || ocpJobs.selectedWorkerCount)
    const [networkType, setNetworkType] = useState(searchParams.get("networkType") || ocpJobs.selectedNetworkType)
    const [version, setVersion] = useState(searchParams.get("version") || ocpJobs.selectedVersion)
    const [jobType, setJobType] = useState(searchParams.get("jobType") || ocpJobs.selectedJobType)
    const [isRehearse, setRehearse] = useState(searchParams.get("isRehearse") || ocpJobs.selectedRehearse)
    const [startDate, setStartDate] = useState(searchParams.get("startDate")  || ocpJobs.startDate) || ""
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || ocpJobs.endDate) || ""

    const sidebarComponents  = [
        {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
        {name: "Ci System", onChange: setCiSystem, value: ciSystem, options: ocpJobs.ciSystems},
        {name: "Platform", onChange: setPlatform, value: platform, options: ocpJobs.platforms},
        {name: "Benchmark", onChange: setBenchmark, value: benchmark, options:ocpJobs.benchmarks },
        {name: "Workers Count", onChange: setWorkerCount, value: workerCount, options:ocpJobs.workers },
        {name: "Network Type", onChange: setNetworkType, value: networkType, options:ocpJobs.networkTypes },
        {name: "Versions", onChange: setVersion, value: version, options: ocpJobs.versions},
        {name: "Job Type", onChange: setJobType, value: jobType, options: ocpJobs.jobTypes},
        {name: "Rehearse", onChange: setRehearse, value: isRehearse, options: ocpJobs.rehearses},
    ]

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(platform !== '') buildParams += `&platform=${platform}`
        if(benchmark !== '') buildParams += `&benchmark=${benchmark}`
        if(version !== '') buildParams += `&version=${version}`
        if(workerCount !== '') buildParams += `&workerCount=${workerCount}`
        if(networkType !== '') buildParams += `&networkType=${networkType}`
        if(jobType !== '') buildParams += `&jobType=${jobType}`
        if(isRehearse !== '') buildParams += `&isRehearse=${isRehearse}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/ocp?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, platform, benchmark, version, workerCount, networkType, startDate, endDate])

    useEffect( ()=>{
        dispatch(updateOCPDataFilter({ciSystem, platform, benchmark, version, workerCount, networkType, jobType, isRehearse}))
    }, [ ciSystem, platform, benchmark, version, workerCount, networkType, , jobType, isRehearse, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            dispatch(fetchOCPJobsData(startDate, endDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        if(endDate === ""){
            setEndDate(ocpJobs.endDate)
            setStartDate(ocpJobs.startDate)
        }
    }, [endDate, setEndDate, setStartDate, ocpJobs.startDate, ocpJobs.endDate])


    return (
        <HomeLayout initialState={ocpJobs.initialState}
                    topHeadersData={topHeadersData} sidebarComponents={sidebarComponents}
                    tableMetaData={ocpJobs.tableData} tableData={ocpJobs.data}
                    expandableComponent={BenchmarkResults} addExpandableRows={true}

        />
    );
}
