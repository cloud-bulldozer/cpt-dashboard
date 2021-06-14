import React from 'react';
import { Card, CardTitle, CardBody, CardFooter } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import useCardData from '../../../hooks/useCardData'
import InstallCard from './Cards/Install'
import ScaleCard from './Cards/Scale'
import UpgradeCard from './Cards/Upgrades'
import BenchmarkCard from './Cards/Benchmarks'
import { Spinner } from '@patternfly/react-core';


export default function Basic(props) {

  const [row, isExpanded] = props.data

  let cardData = useCardData(row, isExpanded)
  if (typeof cardData !== undefined && cardData.length > 0) {
    return (
      <Grid className='demoCard'>
        <GridItem span="5">
          <InstallCard data={ cardData.filter((item) => item.build_tag == "install")[0] } />
        </GridItem>
        <GridItem span="3">
          <ScaleCard data={ cardData.filter((item) => item.build_tag.includes("scale")) } />
        </GridItem>
        <GridItem span="2">
          <BenchmarkCard data={ cardData.filter((item) => !item.build_tag.includes("scale") && item.build_tag != "install" && item.build_tag != "upgrades") } />
        </GridItem>
        <GridItem span="2">
          <UpgradeCard data={ cardData.filter((item) => item.build_tag == "upgrades")[0] } />
        </GridItem>
    
    
      </Grid>
    )
  }
  else {
    return <Grid>No Results Found</Grid>
  }
  
} 
