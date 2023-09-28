import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import useESPerfData from '../../hooks/useESPerfData';
import React from 'react';


export default function JobView() {
  const perfData = useESPerfData("jobs")
  return (
    <>
    <div className="PlatformView">
     <PlatformTabs id="PlatformTabs" data={perfData} />
     </div>
    </>
  );
}
