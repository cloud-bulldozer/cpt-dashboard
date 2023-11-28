
import "../css/PlatformView.css";

import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect, useState} from 'react';
import {useDispatch, useSelector} from "react-redux";
import {HomeLayout} from "../templates/HomeLayout";
import {useHistory, useLocation} from "react-router-dom";
import {updateCPTDataFilter} from "../../store/reducers/CPTJobsReducer";
import {fetchCPTJobsData} from "../../store/Actions/ActionCreator";



export const HomeView = () => {

   const dispatch = useDispatch()
   const history = useHistory();
   const {search} = useLocation();
   const searchParams = new URLSearchParams(search);

   const cptJobs = useSelector(state => state.cptJobs)

  const topHeadersData = [
      {loading: cptJobs.waitForUpdate, title: 'No. Jobs', value: cptJobs.total},
      {loading: cptJobs.waitForUpdate, title: 'Success', value: cptJobs.success},
      {loading: cptJobs.waitForUpdate, title: 'Failure', value: cptJobs.failure},
      {loading: cptJobs.waitForUpdate, title: 'Others', value: cptJobs.others},
  ]

  const [ciSystem, setCiSystem] = useState(searchParams.get("ciSystem") || cptJobs.selectedCiSystem)
  const [product, setProduct] = useState(searchParams.get("product") || cptJobs.selectedProduct)
  const [testName, setTestName] = useState(searchParams.get("testName") || cptJobs.selectedTestName)
  const [jobStatus, setJobStatus] = useState(searchParams.get("jobStatus") || cptJobs.selectedJobStatus)
  const [releaseStream, setReleaseStream] = useState(searchParams.get("releaseStream") || cptJobs.selectedReleaseStream)
  const [startDate, setStartDate] = useState(searchParams.get("startDate") || cptJobs.startDate) || ""
  const [endDate, setEndDate] = useState(searchParams.get("endDate")  || cptJobs.endDate) || ""

  // Changing the URL Route Path
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

  // Update the Components Data
  useEffect( ()=>{
        dispatch(updateCPTDataFilter({ciSystem, product, testName, jobStatus, releaseStream}))
  }, [ ciSystem, product, testName, jobStatus, releaseStream, dispatch ])

  // Fetch the data when startDate/ endDate changes
    useEffect(() => {
        if(startDate || endDate){
            dispatch(fetchCPTJobsData(startDate, endDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        if(endDate === ""){
            setEndDate(cptJobs.endDate)
            setStartDate(cptJobs.startDate)
        }
    }, [endDate, setEndDate, setStartDate, cptJobs.startDate, cptJobs.endDate])
    
  const sidebarComponents = [
      {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
      {name: "CiSystem", options: cptJobs.ciSystems, onChange: setCiSystem, value: ciSystem},
      {name: "Product", options: cptJobs.products, onChange: setProduct, value: product},
      {name: "Test Name", options: cptJobs.testNames, onChange: setTestName, value: testName},
      {name: "Job Status", options: cptJobs.jobStatuses, onChange: setJobStatus, value: jobStatus},
      {name: "Release Stream", options: cptJobs.releaseStreams, onChange: setReleaseStream, value: releaseStream},
  ]

  return (
        <HomeLayout initialState={cptJobs.initialState}
                    topHeadersData={topHeadersData} sidebarComponents={sidebarComponents}
                    tableMetaData={cptJobs.tableData} tableData={cptJobs.data}
                     />
  );
}
