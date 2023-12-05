import {Puff} from "react-loading-icons";
import React from "react";


export const PuffLoad = ({height=12, stroke= "#0000FF", strokeOpacity=.125} ) => {
    return <Puff height={height} stroke={stroke} strokeOpacity={strokeOpacity} />
}

export default PuffLoad;

