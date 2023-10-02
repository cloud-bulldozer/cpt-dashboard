import {Grid, GridItem} from "@patternfly/react-core";
import InstallCard from "../Platform/Table/Cards/Install";
import React from "react";
import {DisplayGrafana} from "./DisplayGrafana";


export const BenchmarkResults = ({dataset, isExpanded}) => {
    return (
        <>
            <Grid className='demoCard' hasGutter>
                <GridItem span={"7"}>
                  <InstallCard data={ dataset }
                               isExpanded={isExpanded} />
                </GridItem>
                <GridItem span={"5"}>
                  <DisplayGrafana benchmarkConfigs={ dataset }
                                  isExpanded={isExpanded} />
                </GridItem>

            </Grid>
        </>
    )
}
