import React from 'react';
import WithLabels from './WithLabels';
import VersionList from './VersionList';
import { Title, TitleSizes } from '@patternfly/react-core';

const OcpPerformanceApp = (props) => {
  const versions = props.data
  return (
    <>
        <Title headingLevel="h1" size={TitleSizes['4xl']}>
          OCP Performance at Scale
        </Title>
        <WithLabels data={versions} />
        <VersionList data={versions} />
    </>
  )
}

export default OcpPerformanceApp