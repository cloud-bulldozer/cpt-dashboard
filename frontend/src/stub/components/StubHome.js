import '../../components/css/PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import React, {useEffect, useState} from 'react';

import {HomeLayout} from "../../components/templates/HomeLayout";
import {useDispatch, useSelector} from "react-redux";
import {useHistory, useLocation} from "react-router-dom";
import {updateStubDataFilter} from "../store/reducers/StubReducer";
import {fetchStubData} from "../store/actions/ActionCreator";



export function StubHome() {

    const dispatch = useDispatch()
    const {search} = useLocation();
    const searchParams = new URLSearchParams(search);
    const history = useHistory();
    const stubData = useSelector(state => state.stubData)

    const [startDate, setStartDate] = useState(searchParams.get("startDate")  || stubData.startDate) || ""
    const [endDate, setEndDate] = useState(searchParams.get("endDate") || stubData.endDate) || ""

    const preloadFilters = (filters) => {
        let results = {}
        for (const [key, value] of Object.entries(filters)) {
            results[value.name] = value.items[0]
        }
        return results
    }

    const [buildComponents, setBuildComponents] = useState(() => preloadFilters(stubData.filtersData))

    const updateSetBuildComponents = (key, value) => {
        setBuildComponents(buildComponents=>({...buildComponents, [key]: value}))
    }

    function buildSideBarComponents() {
        let components = [
            {name: "DateComponent", options: [], onChange: null, value: null, startDate: startDate,  endDate: endDate, setStartDate: setStartDate, setEndDate: setEndDate},
        ];

        for (const [key, value] of Object.entries(stubData.filtersData)) {
            components.push({name: value.display, value: buildComponents[value.name], onChange: updateSetBuildComponents, options: value.items, isKeypair: true})
        }
        return components
    }

    const sidebarComponents  = buildSideBarComponents()

    useEffect(() => {
        let buildParams = ''
        if(startDate !== '') buildParams += `&startDate=${startDate}`
        if(endDate !== '') buildParams += `&endDate=${endDate}`
        history.push(`/stub?${buildParams.substring(1)}`, { replace: true });

    }, [history, startDate, endDate])

    useEffect( ()=>{
        dispatch(updateStubDataFilter({}))
    }, [ dispatch ])

    useEffect(() => {
        if(startDate || endDate){
            dispatch(fetchStubData(startDate, endDate))
        }
    }, [startDate, endDate, dispatch])

    useEffect(() => {
        if(endDate === ""){
            setEndDate(stubData.endDate)
            setStartDate(stubData.startDate)
        }
    }, [endDate, setEndDate, setStartDate, stubData.startDate, stubData.endDate])


    return (
        <HomeLayout initialState={stubData.initialState}
        sidebarComponents={sidebarComponents}
        tableMetaData={stubData.tableData} tableData={stubData.data}
        />
        );
    }
