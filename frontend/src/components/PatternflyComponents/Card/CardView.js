import {
    Card,
    CardBody,
    CardHeader,
    CardTitle
} from "@patternfly/react-core";
import React from "react";
import {Puff} from "react-loading-icons";


export const CardView = ({header, body, initialState, isSelectableRaised=true}) => {
    return (
        <Card>
            <CardHeader>
                {header && <CardTitle>{header}</CardTitle>}
            </CardHeader>
            <CardBody>
                {!initialState && body }
                {initialState && <> <Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</>}
            </CardBody>

        </Card>
    )
}

export default CardView;
