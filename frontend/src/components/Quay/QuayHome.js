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
    const [releaseStream, setReleaseStream] = useState(searchParams.get("releaseStream") || quayJobs.selectedReleaseStream)
    const [hitSize, setHitSize] = useState(searchParams.get("hitSize") || quayJobs.selectedHitSize)
    const [concurrency, setConcurrency] = useState(searchParams.get('concurrency') || quayJobs.selectedConcurrency)
    const [imagePushPulls, setImagePushPulls] = useState(searchParams.get('imagePushPulls') || quayJobs.selectedImagePushPulls)
    const [startDate, setStartDate] = useState(searchParams.get("startDate")  || quayJobs.startDate) || ""
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || quayJobs.endDate) || ""

    const sidebarComponents  = [
        {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
        {name: "Ci System", onChange: setCiSystem, value: ciSystem, options: quayJobs.ciSystems},
        {name: "Platform", onChange: setPlatform, value: platform, options: quayJobs.platforms},
        {name: "Benchmark", onChange: setBenchmark, value: benchmark, options:quayJobs.benchmarks },
        {name: "Release Streams", onChange: setReleaseStream, value: releaseStream, options: quayJobs.releaseStreams},
        {name: "Workers Count", onChange: setWorkerCount, value: workerCount, options:quayJobs.workers },
        {name: "Hit Size", onChange: setHitSize, value: hitSize, options:quayJobs.hitSizes },
        {name: "Concurrency", onChange: setConcurrency, value: concurrency, options:quayJobs.concurrencies },
        {name: "Image Push/Pulls", onChange: setImagePushPulls, value: imagePushPulls, options:quayJobs.imagePushPulls }
    ]

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(platform !== '') buildParams += `&platform=${platform}`
        if(benchmark !== '') buildParams += `&benchmark=${benchmark}`
        if(releaseStream !== '') buildParams += `&releaseStream=${releaseStream}`
        if(workerCount !== '') buildParams += `&workerCount=${workerCount}`
        if(hitSize !== '') buildParams += `&hitSize=${hitSize}`
        if(concurrency !== '') buildParams += `&concurrency=${concurrency}`
        if(imagePushPulls !== '') buildParams += `&imagePushPulls=${imagePushPulls}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/quay?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, platform, benchmark, releaseStream, workerCount, hitSize, concurrency, imagePushPulls, startDate, endDate])

    useEffect( ()=>{
        dispatch(updateQuayDataFilter({ciSystem, platform, benchmark, releaseStream, workerCount, hitSize, concurrency, imagePushPulls}))
    }, [ ciSystem, platform, benchmark, releaseStream, workerCount, hitSize, concurrency, imagePushPulls, dispatch ])

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
