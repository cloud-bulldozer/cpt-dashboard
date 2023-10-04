import Plotly from "react-plotly.js";
import React from "react";


export const PlotlyView = ({data, width, height}) => {
    return <Plotly data={data}
                   layout={{"width": width, "height": height}}
           />
}
