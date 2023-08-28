import './PlatformView.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './Tabs/Platform';
import usePerfData from '../../hooks/usePerfData';
import React from 'react';


export default function PlatformView() {
  const perfData = usePerfData()
  return (
    <>
    <div className="PlatformView">
     <PlatformTabs id="PlatformTabs" data={perfData} />
     </div>
    </>
  );
}

