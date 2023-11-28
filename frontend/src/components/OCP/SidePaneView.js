import {useDispatch, useSelector} from "react-redux";
import {Split, Stack, StackItem} from "@patternfly/react-core";
import CardView from "../PatternflyComponents/Card/CardView";
import React, {useEffect, useState} from "react";
import {FormSelectView} from "../PatternflyComponents/Form/FormSelectView";
import { updateOCPDataFilter} from "../../store/reducers/OCPJobsReducer";
import {fetchOCPJobsData} from "../../store/Actions/ActionCreator";
import {Text4} from "../PatternflyComponents/Text/Text";
import {DatePickerView} from "../PatternflyComponents/Date/DatePickerView";
import {useHistory, useLocation} from "react-router-dom";



export const SidePaneView = () => {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();



    const job_results = useSelector(state => state.ocpJobs)
    const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || job_results.selectedCiSystem)
    const [platform, setPlatform] = useState(searchParams.get("platform") || job_results.selectedPlatform)
    const [benchmark, setBenchmark] = useState(searchParams.get("benchmark") || job_results.selectedBenchmark)
    const [workerCount, setWorkerCount] = useState(searchParams.get("workerCount") || job_results.selectedWorkerCount)
    const [networkType, setNetworkType] = useState(searchParams.get("networkType") || job_results.selectedNetworkType)
    const [version, setVersion] = useState(searchParams.get("version") || job_results.selectedVersion)
    const [startDate, setStartDate] = useState(searchParams.get("startDate") || searchParams.get("") || job_results.startDate)
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || searchParams.get("") || job_results.endDate)


    const stackDetails = [
        {name: "Ci System", onChange: setCiSystem, selectedValue: ciSystem, options: job_results.ciSystems},
        {name: "Platform", onChange: setPlatform, selectedValue: platform, options: job_results.platforms},
        {name: "Benchmark", onChange: setBenchmark, selectedValue: benchmark, options:job_results.benchmarks },
        {name: "Workers Count", onChange: setWorkerCount, selectedValue: workerCount, options:job_results.workers },
        {name: "Network Type", onChange: setNetworkType, selectedValue: networkType, options:job_results.networkTypes },
        {name: "Versions", onChange: setVersion, selectedValue: version, options: job_results.versions},

    ]

    useEffect( ()=>{
        dispatch(updateOCPDataFilter({ciSystem, platform, benchmark, version, workerCount, networkType}))
    }, [ ciSystem, platform, benchmark, version, workerCount, networkType, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            let sDate = startDate || job_results.startDate
            let eDate = endDate || job_results.endDate
            dispatch(fetchOCPJobsData(sDate, eDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(platform !== '') buildParams += `&platform=${platform}`
        if(benchmark !== '') buildParams += `&benchmark=${benchmark}`
        if(version !== '') buildParams += `&version=${version}`
        if(workerCount !== '') buildParams += `&workerCount=${workerCount}`
        if(networkType !== '') buildParams += `&networkType=${networkType}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/ocp?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, platform, benchmark, version, workerCount, networkType, startDate, endDate])


    const DisplayDate = () => {
        return <>
            <Split hasGutter isWrappable>
                <Stack>
                    <StackItem children={<Text4 value={"Start Date"} />} />
                    <StackItem children={<DatePickerView defaultDate={job_results.startDate || startDate} setDate={setStartDate} />}/>
                </Stack>
                <Stack>
                    <StackItem children={<Text4 value={"End Date"} />} />
                    <StackItem children={<DatePickerView defaultDate={job_results.endDate || endDate} setDate={setEndDate} />}/>
                </Stack>
            </Split>
        </>
    }


    return <>
        <Stack hasGutter>
            <StackItem span={3}>

                <CardView body={DisplayDate()}/>
            </StackItem>
            {
                stackDetails.map( item =>
                    <StackItem key={item.name} children={<CardView initialState={job_results.initialState}
                                           header={<Text4 value={item.name} />}
                                           body={<FormSelectView options={item.options}
                                                                 onChange={item.onChange}
                                                                 selectedValue={item.selectedValue}
                                           />}
                                />} />
                )
            }
        </Stack>
    </>
}

