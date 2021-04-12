import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';


const OcpPerformanceHeader = () => {
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