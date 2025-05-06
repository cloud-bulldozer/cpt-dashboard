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

  const getGraphData = (id) => {
    const data = graphDataCopy?.filter((a) => a.uid === id);
    return data;
  };
  const hasGraphData = (uuid) => {
    const hasData = getGraphData(uuid).length > 0;

    return hasData;
  };

  return (
    <>
      {hasGraphData(item.id) ? (
        <Plot
          data={getGraphData(item.id)[0]?.data}
          layout={getGraphData(item.id)[0]?.layout}
          key={uid()}
        />
      ) : isGraphLoading && !hasGraphData(item.id) ? (
        <div className="loader"></div>
      ) : (
        <></>
      )}
    </>
  );
};

ILabGraph.propTypes = {
  item: PropType.object,
};
export default ILabGraph;
