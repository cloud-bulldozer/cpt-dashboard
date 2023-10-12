import Plotly from "react-plotly.js";
import React from "react";


export const PlotlyView = ({data, width = "100%", height = "100%"}) => {
    return <Plotly data={data}
                   useResizeHandler={true}
                   layout={{ responsive: true, autosize: true }}
                   style={{width: {width}, height: {height} }}
           />
}
