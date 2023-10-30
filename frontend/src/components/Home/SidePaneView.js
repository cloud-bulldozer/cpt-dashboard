import {useDispatch, useSelector} from "react-redux";
import {Split, Stack, StackItem} from "@patternfly/react-core";
import CardView from "../PatternflyComponents/Card/CardView";
import React, {useEffect, useState} from "react";
import {FormSelectView} from "../PatternflyComponents/Form/FormSelectView";
import { updateDataFilter} from "../../store/reducers/JobsReducer";
import {fetchJobsData} from "../../store/Actions/ActionCreator";
import {Text4} from "../PatternflyComponents/Text/Text";
import {DatePickerView} from "../PatternflyComponents/Date/DatePickerView";


export const SidePaneView = () => {

    const dispatch = useDispatch()

    const job_results = useSelector(state => state.jobs)
    const [platform, setPlatform] = useState(job_results.selectedPlatform)
    const [benchmark, setBenchmark] = useState(job_results.selectedBenchmark)
    const [workerCount, setWorkerCount] = useState(job_results.selectedWorkerCount)
    const [networkType, setNetworkType] = useState(job_results.selectedNetworkType)
    const [version, setVersion] = useState(job_results.selectedVersion)
    const [ciSystem, setCiSystem] = useState(job_results.selectedCiSystem)
    const [startDate, setStartDate] = useState(job_results.startDate)
    const [endDate, setEndDate] = useState(job_results.endDate)


    const stackDetails = [
        {name: "CiSystem", onChange: setCiSystem, selectedValue: ciSystem, options: job_results.ciSystems},
        {name: "Platform", onChange: setPlatform, selectedValue: platform, options: job_results.platforms},
        {name: "Benchmark", onChange: setBenchmark, selectedValue: benchmark, options:job_results.benchmarks },
        {name: "WorkersCount", onChange: setWorkerCount, selectedValue: workerCount, options:job_results.workers },
        {name: "NetworkType", onChange: setNetworkType, selectedValue: networkType, options:job_results.networkTypes },
        {name: "Versions", onChange: setVersion, selectedValue: version, options: job_results.versions},

    ]

    useEffect( ()=>{
        dispatch(updateDataFilter({ciSystem, platform, benchmark, version, workerCount, networkType}))
    }, [ ciSystem, platform, benchmark, version, workerCount, networkType, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            let sDate = startDate || job_results.startDate
            let eDate = endDate || job_results.endDate
            dispatch(fetchJobsData(sDate, eDate))
        }
    }, [startDate, endDate, dispatch])


    const DisplayDate = () => {
        return <>
            <Split hasGutter isWrappable>
                <Stack>
                    <StackItem children={<Text4 value={"StartDate"} />} />
                    <StackItem children={<DatePickerView defaultDate={job_results.startDate || startDate} setDate={setStartDate} />}/>
                </Stack>
                <Stack>
                    <StackItem children={<Text4 value={"EndDate"} />} />
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

