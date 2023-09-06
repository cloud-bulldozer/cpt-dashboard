import {useDispatch, useSelector} from "react-redux";
import {Split, Stack, StackItem} from "@patternfly/react-core";
import CardView from "../PatternflyComponents/Card/CardView";
import React, {useEffect, useState} from "react";
import {FormSelectView} from "../PatternflyComponents/Form/FormSelectView";
import { updateDataFilter} from "../../store/reducers/JobsReducer";
import {fetchJobsData} from "../../store/Actions/ActionCreator";
import {Text4} from "../PatternflyComponents/Text/Text";


export const SidePaneView = () => {

    const dispatch = useDispatch()
    const [startDate, setStartDate] = useState()
    const [endDate, setEndDate] = useState()

    const job_results = useSelector(state => state.jobs)
    const [platform, setPlatform] = useState(job_results.selectedPlatform)
    const [benchmark, setBenchmark] = useState(job_results.selectedBenchmark)
    const [workerCount, setWorkerCount] = useState(job_results.selectedWorkerCount)
    const [networkType, setNetworkType] = useState(job_results.selectedNetworkType)
    const [version, setVersion] = useState(job_results.selectedVersion)
    const [ciSystem, setCiSystem] = useState(job_results.selectedCiSystem)


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
        dispatch(fetchJobsData(startDate, endDate))
    }, [startDate, endDate, dispatch])


    return <>
        <Stack hasGutter>
            <StackItem span={3}>
                <CardView body={DisplayDate(setStartDate, setEndDate)}/>
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


const DisplayDate = (setStartDate, setEndDate) => {
    return <>
        <Split hasGutter isWrappable>
            {GetStack("StartDate", setStartDate)}
            {GetStack("EndDate", setEndDate)}
        </Split>
    </>
}

const GetStack = (value, onChange) => {
    return <><Stack>
        <StackItem children={<Text4 value={value} />} />
        <StackItem children={<input type={"date"} onChange={(e)=>onChange(e.target.value)} />}/>
    </Stack></>
}
