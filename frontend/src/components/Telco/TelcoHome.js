import '../css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect, useState} from 'react';

import {HomeLayout} from "../templates/HomeLayout";
import {useDispatch, useSelector} from "react-redux";
import {useHistory, useLocation} from "react-router-dom";
import {updateTelcoDataFilter} from "../../store/reducers/TelcoJobsReducer";
import {fetchTelcoJobsData} from "../../store/Actions/ActionCreator";
import {BenchmarkResults} from "./BenchmarkResults";


export function TelcoHome() {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();
    const telcoJobs = useSelector(state => state.telcoJobs)

    const topHeadersData = [
      {loading: telcoJobs.waitForUpdate, title: 'No. Jobs', value: telcoJobs.total},
      {loading: telcoJobs.waitForUpdate, title: 'Success', value: telcoJobs.success},
      {loading: telcoJobs.waitForUpdate, title: 'Failure', value: telcoJobs.failure},
      {loading: telcoJobs.waitForUpdate, title: 'Others', value: telcoJobs.others},
      {loading: telcoJobs.waitForUpdate, title: 'Duration Running', value: telcoJobs.duration}
  ]

    const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || telcoJobs.selectedCiSystem)
    const [benchmark, setBenchmark] = useState(searchParams.get("benchmark") || telcoJobs.selectedBenchmark)
    const [version, setVersion] = useState(searchParams.get("version") || telcoJobs.selectedVersion)
    const [releaseStream, setReleaseStream] = useState(searchParams.get("releaseStream") || telcoJobs.selectedReleaseStream)
    const [formal, setFormal] = useState(searchParams.get("formal") || telcoJobs.selectedFormal)
    const [cpu, setCpu] = useState(searchParams.get("cpu") || telcoJobs.selectedCpu)
    const [nodeName, setNodeName] = useState(searchParams.get("nodeName") || telcoJobs.selectedNodeName)
    const [startDate, setStartDate] = useState(searchParams.get("startDate")  || telcoJobs.startDate) || ""
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || telcoJobs.endDate) || ""

    const sidebarComponents  = [
        {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
        {name: "Ci System", onChange: setCiSystem, value: ciSystem, options: telcoJobs.ciSystems},
        {name: "Benchmark", onChange: setBenchmark, value: benchmark, options: telcoJobs.benchmarks },
        {name: "Versions", onChange: setVersion, value: version, options: telcoJobs.versions},
        {name: "Release Streams", onChange: setReleaseStream, value: releaseStream, options: telcoJobs.releaseStreams},
        {name: "isFormal", onChange: setFormal, value: formal, options: telcoJobs.formals},
        {name: "Cpu", onChange: setCpu, value: cpu, options: telcoJobs.cpus},
        {name: "Node Name", onChange: setNodeName, value: nodeName, options: telcoJobs.nodeNames},
    ]

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(benchmark !== '') buildParams += `&benchmark=${benchmark}`
        if(version !== '') buildParams += `&version=${version}`
        if(releaseStream !== '') buildParams += `&releaseStream=${releaseStream}`
        if(formal !== '') buildParams += `&formal=${formal}`
        if(cpu !== '') buildParams += `&cpu=${cpu}`
        if(nodeName !== '') buildParams += `&nodeName=${nodeName}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/telco?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, benchmark, version, releaseStream, formal, cpu, nodeName, startDate, endDate])

    useEffect( ()=>{
        dispatch(updateTelcoDataFilter({ciSystem, benchmark, version, releaseStream, formal, cpu, nodeName}))
    }, [ ciSystem, benchmark, version, releaseStream, formal, cpu, nodeName, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            dispatch(fetchTelcoJobsData(startDate, endDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        if(endDate === ""){
            setEndDate(telcoJobs.endDate)
            setStartDate(telcoJobs.startDate)
        }
    }, [endDate, setEndDate, setStartDate, telcoJobs.startDate, telcoJobs.endDate])


    return (
        <HomeLayout initialState={telcoJobs.initialState}
                    topHeadersData={topHeadersData} sidebarComponents={sidebarComponents}
                    tableMetaData={telcoJobs.tableData} tableData={telcoJobs.data}
                    expandableComponent={BenchmarkResults} addExpandableRows={true}
        />
    );
}
