import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from "react-redux";
import {fetchProwCIData} from "../../store/Actions/ActionCreator";
import {Puff} from "react-loading-icons";


export default function JobView() {
   const dispatch = useDispatch();
    const prowci = useSelector(state => state.prowci);
    useEffect(() => {
        dispatch(fetchProwCIData())
    }, [dispatch])
  return (
    <>
    <div className="PlatformView">
     { prowci.initialState &&  <> <Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</> }
     { !prowci.initialState &&  <PlatformTabs id="PlatformTabs" data={prowci.response} /> }
     </div>
    </>
  );
}

