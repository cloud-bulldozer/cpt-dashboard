import {Grid, GridItem} from "@patternfly/react-core";
import InstallCard from "./InstallCard";
import React from "react";
import {DisplayGraph} from "./DisplayGraph";


export const BenchmarkResults = ({dataset, isExpanded}) => {
    return (
        <> {
            ( isExpanded &&
                <Grid className='demoCard' hasGutter>
                    <GridItem span={"6"}>
                      <InstallCard data={ dataset }
                                   isExpanded={isExpanded} />
                    </GridItem>
                    <GridItem span={"6"}>
                      <DisplayGraph uuid={ dataset.uuid }
                                    resultKey={'apiResults'}
                                    heading={"Quay API Status Codes"} />
                    </GridItem>
                    <GridItem span={"6"}>
                      <DisplayGraph uuid={ dataset.uuid }
                                    resultKey={'imageResults'}
                                    heading={"Quay Image Status Codes"} />
                    </GridItem>
                    <GridItem span={"6"}>
                      <DisplayGraph uuid={ dataset.uuid }
                                    resultKey={'latencyResults'}
                                    heading={"Quay Latencies"} />
                    </GridItem>
                </Grid>
            ) || <>NO Data</>
        }
        </>
    )
}
