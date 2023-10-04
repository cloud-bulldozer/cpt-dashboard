import {Split, SplitItem} from "@patternfly/react-core";


export const SplitView = ({splitValues}) => {
    return (
        <>
            <Split hasGutter>
                {
                    splitValues &&
                    splitValues.map( (value, index) =>
                        <SplitItem key={index} children={value}/>
                    )
                }
            </Split>
        </>
    )
}
