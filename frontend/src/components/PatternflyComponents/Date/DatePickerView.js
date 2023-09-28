import {DatePicker} from "@patternfly/react-core";
import React from "react";


export const DatePickerView = ({defaultDate, setDate, ...props}) => {
    return <DatePicker {...props} value={defaultDate} onChange={(_e, value)=>setDate(value)} />
}