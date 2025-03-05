import "./index.less";

import {
  Button,
  Menu,
  MenuContent,
  MenuItem,
  MenuItemAction,
  MenuList,
  Title,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import { InfoCircleIcon } from "@patternfly/react-icons";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";
import RenderPagination from "@/components/organisms/Pagination";
import { cloneDeep } from "lodash";
import { handleMultiGraph } from "@/actions/ilabActions.js";
import { uid } from "@/utils/helper";
import { useState } from "react";

const IlabCompareComponent = () => {
  // const { data } = props;
  const { page, perPage, totalItems, tableData } = useSelector(
    (state) => state.ilab
  );
  const dispatch = useDispatch();
  const [selectedItems, setSelectedItems] = useState([]);
  const { multiGraphData } = useSelector((state) => state.ilab);
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);
  const graphDataCopy = cloneDeep(multiGraphData);

  const onSelect = (_event, itemId) => {
    const item = itemId;
    if (selectedItems.includes(item)) {
      setSelectedItems(selectedItems.filter((id) => id !== item));
    } else {
      setSelectedItems([...selectedItems, item]);
    }
  };
  const dummy = () => {
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
                      <MenuItemAction
                        icon={<InfoCircleIcon aria-hidden />}
                        actionId="code"
                        onClick={() => console.log("clicked on code icon")}
                        aria-label="Code"
                      />
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
      <div className="chart-container">
        {isGraphLoading ? (
          <div className="loader"></div>
        ) : graphDataCopy?.length > 0 &&
          graphDataCopy?.[0]?.data?.length > 0 ? (
          <div className="chart-box">
            <Plot
              data={graphDataCopy[0]?.data}
              layout={graphDataCopy[0]?.layout}
              key={uid()}
            />
          </div>
        ) : (
          <div>No data to compare</div>
        )}
      </div>
    </div>
  );
};

IlabCompareComponent.propTypes = {
  data: PropTypes.array,
};
export default IlabCompareComponent;
