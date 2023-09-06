import {Accordion, AccordionContent, AccordionItem} from "@patternfly/react-core";
import React from "react";


export const AccordionView = ({childComponent}) =>{
    return (
        <Accordion>
            <AccordionItem>
                <AccordionContent>
                    {childComponent}
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    )
}
export default AccordionView
