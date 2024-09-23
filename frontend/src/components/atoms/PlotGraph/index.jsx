import Plotly from "react-plotly.js";
import PropTypes from "prop-types";
const PlotGraph = (props) => {
  return (
    <Plotly
      data={props?.data}
      useResizeHandler={false}
      layout={props?.layout}
      // layout={{ responsive: false, autosize: false, width: 600, length: 600 }}
    />
  );
};
export default PlotGraph;

PlotGraph.propTypes = {
  data: PropTypes.arr,
  layout: PropTypes.object,
};
