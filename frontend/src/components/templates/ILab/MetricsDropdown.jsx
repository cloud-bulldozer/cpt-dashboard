import {
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
  Skeleton
} from "@patternfly/react-core";
import { fetchGraphData, fetchSummaryData, setSelectedMetrics } from "@/actions/ilabActions";
import { useDispatch, useSelector } from "react-redux";

import PropTypes from "prop-types";
import { cloneDeep } from "lodash";
import { uid } from "@/utils/helper";
import { useState } from "react";

const MetricsSelect = (props) => {
  const { metrics, metrics_selected } = useSelector((state) => state.ilab);
  const { item } = props;
  /* Metrics select */
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch();
  // const [selected, setSelected] = useState("Select a value");

  const toggle1 = (toggleRef, selected) => (
    <MenuToggle
      ref={toggleRef}
      onClick={onToggleClick}
      isExpanded={isOpen}
      style={{
        width: "200px",
      }}
    >
      {selected}
    </MenuToggle>
  );

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };
  const onSelect = (_event, value) => {
    console.log("selected", value);
    const [run, metric] = value;
    dispatch(setSelectedMetrics(run, metric));
    dispatch(fetchGraphData(run, metric));
    dispatch(fetchSummaryData(run, metric));
    setIsOpen(false);
  };
  const metricsDataCopy = cloneDeep(metrics);

  const getMetricsData = (id) => {
    const data = metricsDataCopy?.filter((a) => a.uid === id);
    return data;
  };
  const hasMetricsData = (uuid) => {
    const hasData = getMetricsData(uuid).length > 0;

    return hasData;
  };
  /* Metrics select */
  return (
    <>
      {hasMetricsData(item.id) ? (
        <Select
          id="single-select"
          isOpen={isOpen}
          selected={metrics_selected[item.id]}
          onSelect={onSelect}
          onOpenChange={(isOpen) => setIsOpen(isOpen)}
          toggle={(ref) => toggle1(ref, metrics_selected[item.id])}
          shouldFocusToggleOnSelect
        >
          <SelectList>
            {getMetricsData(item.id)[0]?.metrics.map((metric) => (
              <SelectOption
                key={uid()}
                value={[item.id, metric]}
              >
                {metric}
              </SelectOption>
            ))}
          </SelectList>
        </Select>
      ):
      <Skeleton width="33%" screenreaderText="Loaded 33% of content" />
      }
    </>
  );
};

MetricsSelect.propTypes = {
  item: PropTypes.object,
};
export default MetricsSelect;
