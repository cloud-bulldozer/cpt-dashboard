import {
    Grid,
    GridItem
} from "@patternfly/react-core";
import CardView from "../PatternflyComponents/Card/CardView";
import {Text4} from "../PatternflyComponents/Text/Text";
import React from "react";
import { useSelector } from "react-redux";
import {Puff} from "react-loading-icons";


export const TopView = () => {

    const job_results = useSelector(state => state.jobs)

    const cardBody = [job_results.total, job_results.success, job_results.failure, job_results.others]
    const cardHeader= ["No. Jobs", "Success", "Failure", "Others"]



    return <>
        <Grid hasGutter={true} span={2}>
            {
                cardHeader.map( (item, index) =>
                        <GridItem key={index}>
                            <CardView initialState={job_results.initialState}
                                      header={<Text4 value={<span>{item} {job_results.waitForUpdate && <Puff height={12} stroke="#0000FF" strokeOpacity={.125}/>}</span>} />}
                                      body={cardBody[index]} />
                        </GridItem> )
            }
        </Grid>
    </>
}
