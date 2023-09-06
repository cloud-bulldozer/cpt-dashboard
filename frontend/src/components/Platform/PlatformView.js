import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from "react-redux";
import {fetchAirflowData} from "../../store/Actions/ActionCreator";
import {Puff} from "react-loading-icons";


export default function PlatformView() {
    const dispatch = useDispatch();
    const airflow = useSelector(state => state.airflow);
    useEffect(() => {
        dispatch(fetchAirflowData())
    }, [dispatch])
  return (
    <>
    <div className="PlatformView">
     { airflow.initialState &&  <> <Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</> }
     { !airflow.initialState &&  <PlatformTabs id="PlatformTabs" data={airflow.response} /> }
     </div>
    </>
  );
}