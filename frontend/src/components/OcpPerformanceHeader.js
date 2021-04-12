import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import SimpleTabs from './PerformanceTabs';


const OcpPerformanceHeader = (props) => {
  const versions = props.data
  return (
    <> 
        <img className="OcpPerformanceTable-logo" src="logo.png" alt="Openshift Logo"/>
        <Title headingLevel="h1" size={TitleSizes['4xl']}>
          Openshift Performance and Scale Nightlies 
        </Title>
    </>
  )
}

export default OcpPerformanceHeader