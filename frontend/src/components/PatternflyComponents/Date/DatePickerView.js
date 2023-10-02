import {DatePicker} from "@patternfly/react-core";
import React from "react";


export const DatePickerView = ({defaultDate, setDate, ...props}) => {
    return <DatePicker {...props}
                       appendTo={() => document.body}
                       value={defaultDate}
                       onChange={(_e, value)=>setDate(value)}
                       placement="right"
    />
}
