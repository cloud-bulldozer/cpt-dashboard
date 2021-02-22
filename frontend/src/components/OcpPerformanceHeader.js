import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import SimpleTabs from './PerformanceTabs';


const OcpPerformanceHeader = (props) => {
  const versions = props.data
  return (
    <>
        <Title headingLevel="h1" size={TitleSizes['4xl']}>
          All Your Base (are) Belong To Keith
        </Title>
        <SimpleTabs data={versions} />
    </>
  )
}

export default OcpPerformanceHeader