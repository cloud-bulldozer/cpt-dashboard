import "./index.less";

import * as CONSTANTS from "@/assets/constants/metadataConstants";

import { Card, CardBody, Grid, GridItem, Title } from "@patternfly/react-core";

import MetadataRow from "../MetaDataRow";
import PlotGraph from "@/components/atoms/PlotGraph";
import PropTypes from "prop-types";
import TasksInfo from "@/components/molecules/TasksInfo";
import { uid } from "@/utils/helper.js";
import { useMemo } from "react";
import { useSelector } from "react-redux";

const RowContent = (props) => {
  const getGraphData = (uuid) => {
    const data = props.graphData?.filter((a) => a.uuid === uuid);

    return data;
  };
  const hasGraphData = (uuid) => {
    const hasData = getGraphData(uuid).length > 0;

    return hasData;
  };

  const content = useMemo(() => {
    return [
      { heading: "Cluster config", category: CONSTANTS.CLUSTER },
      { heading: "Node Type", category: CONSTANTS.NODE_TYPE },
      { heading: "Node Count", category: CONSTANTS.NODE_COUNT },
    ];
  }, []);
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);

  const graphTitle = useMemo(() => {
    return {
      apiResults: CONSTANTS.API_RESULTS,
      latencyResults: CONSTANTS.LATENCY_RESULTS,
      imageResults: CONSTANTS.IMAGE_RESULTS,
    };
  }, []);
  return (
    <Grid hasGutter>
      <GridItem span={3}>
        <Card>
          <CardBody>
            {content.map((unit) => (
              <>
                <MetadataRow
                  key={uid()}
                  heading={unit.heading}
                  metadata={props.item}
                  category={unit.category}
                  type={props.type}
                />
                <div className="divider" />
              </>
            ))}
            <Title headingLevel="h4" className="type_heading">
              Tasks ran
            </Title>
            <TasksInfo config={props.item} type={props.type} />
          </CardBody>
        </Card>
      </GridItem>
      <GridItem span={5}>
        <Card>
          <CardBody>
            {isGraphLoading && !hasGraphData(props.item.uuid) ? (
              <div className="loader"></div>
            ) : hasGraphData(props.item.uuid) ? (
              getGraphData(props.item.uuid)[0]?.data.length === 0 ? (
                <div>No data to plot</div>
              ) : (
                getGraphData(props.item.uuid)[0]?.data?.map((bit) => {
                  return (
                    <>
                      <Title headingLevel="h4">
                        {graphTitle[bit[0]] ?? bit[0]}
                      </Title>
                      <PlotGraph data={bit[1]} key={uid()} />
                    </>
                  );
                })
              )
            ) : (
              <div>No data to plot</div>
            )}
          </CardBody>
        </Card>
      </GridItem>
    </Grid>
  );
};

export default RowContent;

RowContent.propTypes = {
  item: PropTypes.object,
  type: PropTypes.string,
  graphData: PropTypes.array,
};
