import {
    Card,
    CardBody, CardExpandableContent,
    CardHeader,
    CardTitle
} from "@patternfly/react-core";
import React from "react";
import {Puff} from "react-loading-icons";


export const CardView = ({header, body, initialState=false, isSelectableRaised=true,
                         isExpanded=false, onExpand, expandView=false}) => {

    const cardBody = <CardBody>
                                {!initialState && body }
                                {initialState && <> <Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</>}
                            </CardBody>

    const toggleButtonProps = expandView ?
                                            {
                                                id: 'toggle-button',
                                                'aria-label': 'Details',
                                                'aria-labelledby': 'titleId toggle-button',
                                                'aria-expanded': isExpanded
                                            } : {}

    return (
        <Card  isExpanded={isExpanded}>
            <CardHeader onExpand={onExpand && onExpand || null} toggleButtonProps={toggleButtonProps}>
                {header && <CardTitle>{header}</CardTitle>}
            </CardHeader>
            {
                expandView && <CardExpandableContent children={cardBody}   /> || cardBody
            }
        </Card>
    )
}

export default CardView;
