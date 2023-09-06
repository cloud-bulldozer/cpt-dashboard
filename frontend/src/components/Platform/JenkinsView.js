import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from "react-redux";
import {fetchJenkinsData} from "../../store/Actions/ActionCreator";
import {Puff} from "react-loading-icons";


export default function JenkinsView() {
  // const perfData = useESPerfData("jenkins")

    const dispatch = useDispatch()
    const jenkins = useSelector(state => state.jenkins)
    useEffect(() => {
        dispatch(fetchJenkinsData())
    }, [dispatch])
  return (
    <>
    <div className="PlatformView">
        { jenkins.initialState &&  <> <Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</> }
        { !jenkins.initialState &&  <PlatformTabs id="PlatformTabs" data={jenkins.response} /> }
     </div>
    </>
  );
}

