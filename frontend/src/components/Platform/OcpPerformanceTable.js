import './OcpPerformanceTable.css';
import "@patternfly/react-core/dist/styles/base.css";
import PlatformTabs from './PlatformTabs';
import usePerfData from '../../hooks/usePerfData';
import { Grid, GridItem } from '@patternfly/react-core';

import React, { useState, useEffect } from 'react';


export default function OcpPerformanceTable() {
  const perfData = usePerfData()
  return (
    <>   
    <Grid className="OCPPerformanceTable">
      <GridItem><PlatformTabs id="PlatformTabs" data={perfData} /></GridItem>
      
    </Grid>
    </>
  );
}

