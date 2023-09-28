import {
    Text, TextVariants
} from "@patternfly/react-core";

export const Text1 = ({value, ...props}) => {
    return <><Text component={TextVariants.h1}  children={value} {...props}/></>
}

export const Text2 = ({value, ...props}) => {
    return <><Text component={TextVariants.h2}  children={value} {...props}/></>
}

export const Text3 = ({value, ...props}) => {
    return <><Text component={TextVariants.h3}  children={value} {...props}/></>
}

export const Text4 = ({value, ...props}) => {
    return <><Text style={{color: '#EE0000'}} component={TextVariants.h4}  children={value} {...props}/></>
}

export const Text5 = ({value, ...props}) => {
    return <><Text component={TextVariants.h5}  children={value} {...props}/></>
}

export const Text6 = ({value, ...props}) => {
    return <><Text component={TextVariants.h6}  children={value} {...props}/></>
}
