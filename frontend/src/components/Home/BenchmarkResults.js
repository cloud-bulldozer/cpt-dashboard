import {Grid, GridItem} from "@patternfly/react-core";
import InstallCard from "../Platform/Table/Cards/Install";
import React from "react";


export const BenchmarkResults = ({dataset}) => {
    return (
        <>
            <Grid className='demoCard' hasGutter>
                <GridItem span={"7"}>
                  <InstallCard data={ dataset } />
                </GridItem>
            </Grid>
        </>
    )
}
