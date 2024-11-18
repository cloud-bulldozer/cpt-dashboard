import "./index.less";

import {
  Button,
  Menu,
  MenuContent,
  MenuItem,
  MenuList,
  Popover,
  Stack,
  StackItem,
  Title,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import { InfoCircleIcon } from "@patternfly/react-icons";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";
import RenderPagination from "@/components/organisms/Pagination";
import { cloneDeep } from "lodash";
import {
  fetchPeriods,
  handleMultiGraph,
  handleSummaryData,
  fetchMetricsInfo,
} from "@/actions/ilabActions.js";
import { uid } from "@/utils/helper";
import { useState } from "react";
import ILabSummary from "./ILabSummary";
import ILabMetadata from "./ILabMetadata";
import MetricsSelect from "./MetricsDropdown";

const IlabCompareComponent = () => {
  const { page, perPage, totalItems, tableData } = useSelector(
    (state) => state.ilab
  );
  const dispatch = useDispatch();
  const [selectedItems, setSelectedItems] = useState([]);
  const { multiGraphData, summaryData, isSummaryLoading } = useSelector(
    (state) => state.ilab
  );
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);
  const graphDataCopy = cloneDeep(multiGraphData);

  const onSelect = (_event, itemId) => {
    const item = itemId;
    if (selectedItems.includes(item)) {
      setSelectedItems(selectedItems.filter((id) => id !== item));
    } else {
      setSelectedItems([...selectedItems, item]);
      dispatch(fetchPeriods(item));
      dispatch(fetchMetricsInfo(item));
    }
  };
  const dummy = () => {
    dispatch(handleSummaryData(selectedItems));
    dispatch(handleMultiGraph(selectedItems));
  };
  return (
    <div className="comparison-container">
      <div className="metrics-container">
        <Title headingLevel="h3" className="title">
          Metrics
        </Title>
        <Button
          className="compare-btn"
          isDisabled={selectedItems.length < 2}
          isBlock
          onClick={dummy}
        >
          Compare
        </Button>
        <Menu onSelect={onSelect} selected={selectedItems}>
          <MenuContent>
            <MenuList>
              {tableData.map((item) => {
                return (
                  <MenuItem
                    key={uid()}
                    hasCheckbox
                    itemId={item.id}
                    isSelected={selectedItems.includes(item.id)}
                    actions={
                      <Popover
                        triggerAction="hover"
                        aria-label="Metadata popover"
                        headerContent={<b>Metadata</b>}
                        appendTo={() => document.body}
                        hasNoPadding
                        position="auto"
                        className="mini-metadata"
                        bodyContent={
                          <div position="auto" className="mini-metadata">
                            <ILabMetadata item={item} />
                          </div>
                        }
                      >
                        <Button icon={<InfoCircleIcon aria-hidden />}></Button>
                      </Popover>
                    }
                  >
                    {`${new Date(item.begin_date).toLocaleDateString()} ${
                      item.primary_metrics[0]
                    }`}
                  </MenuItem>
                );
              })}
            </MenuList>
          </MenuContent>
        </Menu>
        <RenderPagination
          items={totalItems}
          page={page}
          perPage={perPage}
          type={"ilab"}
        />
      </div>
      <Stack hasGutter>
        <StackItem span={12} className="metrics-select">
          <MetricsSelect ids={selectedItems} />
        </StackItem>
        <StackItem span={12} className="summary-box">
          {isSummaryLoading ? (
            <div className="loader"></div>
          ) : summaryData.filter((i) => selectedItems.includes(i.uid)).length ==
            selectedItems.length ? (
            <ILabSummary ids={selectedItems} />
          ) : (
            <div>No data to summarize</div>
          )}
        </StackItem>
        <StackItem span={12} className="chart-box">
          {isGraphLoading ? (
            <div className="loader"></div>
          ) : graphDataCopy?.length > 0 &&
            graphDataCopy?.[0]?.data?.length > 0 ? (
            <Plot
              data={graphDataCopy[0]?.data}
              layout={graphDataCopy[0]?.layout}
              key={uid()}
            />
          ) : (
            <div>No data to compare</div>
          )}
        </StackItem>
      </Stack>
    </div>
  );
};

IlabCompareComponent.propTypes = {
  data: PropTypes.array,
};
export default IlabCompareComponent;
