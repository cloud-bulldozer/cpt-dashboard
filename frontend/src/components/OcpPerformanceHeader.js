import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import SimpleTabs from './PerformanceTabs';


const OcpPerformanceHeader = (props) => {
  const versions = props.data
  return (
    <>
        <Title headingLevel="h1" size={TitleSizes['4xl']}>
          OCP Performance at Scale
        </Title>
        <SimpleTabs data={versions} />
    </>
  )
}

export default OcpPerformanceHeader