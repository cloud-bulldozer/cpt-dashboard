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
                </Grid>
            ) || <>NO Data</>
        }
        </>
    )
}
