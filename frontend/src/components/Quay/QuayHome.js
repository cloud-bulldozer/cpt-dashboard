import '../css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect, useState} from 'react';

import {HomeLayout} from "../templates/HomeLayout";
import {useDispatch, useSelector} from "react-redux";
import {useHistory, useLocation} from "react-router-dom";
import {updateQuayDataFilter} from "../../store/reducers/QuayJobsReducer";
import {fetchQuayJobsData} from "../../store/Actions/ActionCreator";
import {BenchmarkResults} from "./BenchmarkResults";


export function QuayHome() {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();
    const quayJobs = useSelector(state => state.quayJobs)

    const topHeadersData = [
      {loading: quayJobs.waitForUpdate, title: 'No. Jobs', value: quayJobs.total},
      {loading: quayJobs.waitForUpdate, title: 'Success', value: quayJobs.success},
      {loading: quayJobs.waitForUpdate, title: 'Failure', value: quayJobs.failure},
      {loading: quayJobs.waitForUpdate, title: 'Others', value: quayJobs.others},
      {loading: quayJobs.waitForUpdate, title: 'Duration Running', value: quayJobs.duration}
  ]

    const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || quayJobs.selectedCiSystem)
    const [platform, setPlatform] = useState(searchParams.get("platform") || quayJobs.selectedPlatform)
    const [benchmark, setBenchmark] = useState(searchParams.get("benchmark") || quayJobs.selectedBenchmark)
    const [workerCount, setWorkerCount] = useState(searchParams.get("workerCount") || quayJobs.selectedWorkerCount)
    const [version, setVersion] = useState(searchParams.get("version") || quayJobs.selectedVersion)
    const [startDate, setStartDate] = useState(searchParams.get("startDate")  || quayJobs.startDate) || ""
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || quayJobs.endDate) || ""

    const sidebarComponents  = [
        {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
        {name: "Ci System", onChange: setCiSystem, value: ciSystem, options: quayJobs.ciSystems},
        {name: "Platform", onChange: setPlatform, value: platform, options: quayJobs.platforms},
        {name: "Benchmark", onChange: setBenchmark, value: benchmark, options:quayJobs.benchmarks },
        {name: "Versions", onChange: setVersion, value: version, options: quayJobs.versions},
        {name: "Workers Count", onChange: setWorkerCount, value: workerCount, options:quayJobs.workers }
    ]

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(platform !== '') buildParams += `&platform=${platform}`
        if(benchmark !== '') buildParams += `&benchmark=${benchmark}`
        if(version !== '') buildParams += `&version=${version}`
        if(workerCount !== '') buildParams += `&workerCount=${workerCount}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/quay?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, platform, benchmark, version, workerCount, startDate, endDate])

    useEffect( ()=>{
        dispatch(updateQuayDataFilter({ciSystem, platform, benchmark, version, workerCount}))
    }, [ ciSystem, platform, benchmark, version, workerCount, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            dispatch(fetchQuayJobsData(startDate, endDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        if(endDate === ""){
            setEndDate(quayJobs.endDate)
            setStartDate(quayJobs.startDate)
        }
    }, [endDate, setEndDate, setStartDate, quayJobs.startDate, quayJobs.endDate])


    return (
        <HomeLayout initialState={quayJobs.initialState}
                    topHeadersData={topHeadersData} sidebarComponents={sidebarComponents}
                    tableMetaData={quayJobs.tableData} tableData={quayJobs.data}
                    expandableComponent={BenchmarkResults} addExpandableRows={true}

        />
    );
}
