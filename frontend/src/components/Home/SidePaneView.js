import {useDispatch, useSelector} from "react-redux";
import {Split, Stack, StackItem} from "@patternfly/react-core";
import CardView from "../PatternflyComponents/Card/CardView";
import React, {useEffect, useState} from "react";
import {FormSelectView} from "../PatternflyComponents/Form/FormSelectView";
import {updateCPTDataFilter} from "../../store/reducers/CPTJobsReducer";
import {fetchCPTJobsData} from "../../store/Actions/ActionCreator";
import {Text4} from "../PatternflyComponents/Text/Text";
import {DatePickerView} from "../PatternflyComponents/Date/DatePickerView";
import {useHistory, useLocation} from "react-router-dom";



export const SidePaneView = () => {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();



    const job_results = useSelector(state => state.cptJobs)
    const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || job_results.selectedCiSystem)
    const [product, setProduct] = useState(searchParams.get("product") || job_results.selectedProduct)
    const [testName, setTestName] = useState(searchParams.get("testName") || job_results.selectedTestName)
    const [jobStatus, setJobStatus] = useState(searchParams.get("jobStatus") || job_results.selectedJobStatus)
    const [releaseStream, setReleaseStream] = useState(searchParams.get("releaseStream") || job_results.selectedReleaseStream)
    const [startDate, setStartDate] = useState(searchParams.get("startDate") || searchParams.get("") || job_results.startDate)
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || searchParams.get("") || job_results.endDate)


    const stackDetails = [
        {name: "CiSystem", onChange: setCiSystem, selectedValue: ciSystem, options: job_results.ciSystems},
        {name: "Product", onChange: setProduct, selectedValue: product, options: job_results.products},
        {name: "Test Name", onChange: setTestName, selectedValue: testName, options: job_results.testNames },
        {name: "Job Status", onChange: setJobStatus, selectedValue: jobStatus, options: job_results.jobStatuses },
        {name: "Release Stream", onChange: setReleaseStream, selectedValue: releaseStream, options: job_results.releaseStreams },
    ]

    useEffect( ()=>{
        dispatch(updateCPTDataFilter({ciSystem, product, testName, jobStatus, releaseStream}))
    }, [ ciSystem, product, testName, jobStatus, releaseStream, dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            let sDate = startDate || job_results.startDate
            let eDate = endDate || job_results.endDate
            dispatch(fetchCPTJobsData(sDate, eDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        let buildParams = ''
        if(ciSystem !== '') buildParams += `&ciSystem=${ciSystem}`
        if(product !== '') buildParams += `&product=${product}`
        if(testName !== '') buildParams += `&testName=${testName}`
        if(jobStatus !== '') buildParams += `&jobStatus=${jobStatus}`
        if(releaseStream !== '') buildParams += `&releaseStream=${releaseStream}`
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/home?${buildParams.substring(1)}`, { replace: true });

    }, [history, ciSystem, product, testName, jobStatus, releaseStream, startDate, endDate])


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

