import "./index.less";

import * as CONSTANTS from "@/assets/constants/metadataConstants";

import { Card, CardBody, Grid, GridItem, Title } from "@patternfly/react-core";
import React, { useMemo } from "react";

import MetadataRow from "../MetaDataRow";
import PlotGraph from "@/components/atoms/PlotGraph";
import PropTypes from "prop-types";
import TasksInfo from "@/components/molecules/TasksInfo";
import { useSelector } from "react-redux";

const content = [
  {
    heading: "Cluster config",
    category: CONSTANTS.CLUSTER,
    key: "cluster-config",
  },
  { heading: "Node Type", category: CONSTANTS.NODE_TYPE, key: "node-type" },
  {
    heading: "Node Count",
    category: CONSTANTS.NODE_COUNT,
    key: "node-count",
  },
];

const graphTitle = {
  apiResults: CONSTANTS.API_RESULTS,
  latencyResults: CONSTANTS.LATENCY_RESULTS,
  imageResults: CONSTANTS.IMAGE_RESULTS,
};

const RowContent = (props) => {
  const graphData = useMemo(() => {
    return props.graphData?.filter((a) => a.uuid === props.item.uuid) || [];
  }, [props.graphData, props.item.uuid]);

  const hasGraphData = graphData.length > 0;
  const firstGraphEntry = graphData[0]?.data || [];
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);

  return (
    <Grid hasGutter>
      <GridItem span={3}>
        <Card>
          <CardBody>
            {content.map((unit) => (
              <React.Fragment key={unit.key}>
                <MetadataRow
                  heading={unit.heading}
                  metadata={props.item}
                  category={unit.category}
                  type={props.type}
                />
                <div className="divider" />
              </React.Fragment>
            ))}
            <Title headingLevel="h4" className="type_heading">
              Tasks ran
            </Title>
            <TasksInfo config={props.item} type={props.type} />
          </CardBody>
        </Card>
      </GridItem>
      <GridItem span={6}>
        <Card>
          <CardBody>
            {isGraphLoading && !hasGraphData ? (
              <div className="loader"></div>
            ) : hasGraphData ? (
              firstGraphEntry.length === 0 ? (
                <div>No data to plot</div>
              ) : (
                firstGraphEntry.map((bit) => (
                  <React.Fragment key={bit[0]}>
                    <Title headingLevel="h4">
                      {graphTitle[bit[0]] ?? bit[0]}
                    </Title>
                    <PlotGraph data={bit[1]} />
                  </React.Fragment>
                ))
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
