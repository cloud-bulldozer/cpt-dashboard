import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import useProwPerfData from '../../hooks/useProwPerfData';
import React from 'react';


export default function JobView() {
  const perfData = useProwPerfData()
  return (
    <>
    <div className="PlatformView">
     <PlatformTabs id="PlatformTabs" data={perfData} />
     </div>
    </>
  );
}

