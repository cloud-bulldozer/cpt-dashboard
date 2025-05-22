import Plot from "react-plotly.js";
import PropType from "prop-types";
import { cloneDeep } from "lodash";
import { uid } from "@/utils/helper";
import { useSelector } from "react-redux";

const ILabGraph = (props) => {
  const { item } = props;
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);
  const { graphData } = useSelector((state) => state.ilab);

  const graphDataCopy = cloneDeep(graphData);

  const currentGraph = graphDataCopy?.find((a) => a.uid === item.id);
  if (currentGraph) {
    return (
      <Plot
        data={currentGraph.data}
        layout={currentGraph.layout}
        key={uid()}
        style={{ width: "100%", height: "100%" }}
      />
    );
  }

  if (isGraphLoading) {
    return <div className="loader"></div>;
  }

  return <></>;
};

ILabGraph.propTypes = {
  item: PropType.object,
};
export default ILabGraph;
