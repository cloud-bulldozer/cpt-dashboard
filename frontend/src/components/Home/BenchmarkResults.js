import {Grid, GridItem} from "@patternfly/react-core";
import InstallCard from "../Platform/Table/Cards/Install";
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
                                    benchmark={dataset.benchmark}
                                     />
                    </GridItem>

                </Grid>
            ) || <>NO Data</>
        }

        </>
    )
}
