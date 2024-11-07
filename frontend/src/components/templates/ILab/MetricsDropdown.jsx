import {
  Badge,
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
  Skeleton,
} from "@patternfly/react-core";
import {
  fetchGraphData,
  fetchSummaryData,
  toggleSelectedMetric,
} from "@/actions/ilabActions";
import { useDispatch, useSelector } from "react-redux";

import PropTypes from "prop-types";
import { cloneDeep } from "lodash";
import { uid } from "@/utils/helper";
import { useState } from "react";

const MetricsSelect = (props) => {
  const { metrics, metrics_selected } = useSelector((state) => state.ilab);
  const { item } = props;
  var current_metrics = metrics_selected[item.id]
    ? metrics_selected[item.id]
    : [];

  /* Metrics select */
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch();

  const toggle1 = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      onClick={onToggleClick}
      isExpanded={isOpen}
      badge={<Badge isRead>{`${current_metrics.length} selected`}</Badge>}
    >
      Additional metrics
    </MenuToggle>
  );

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };
  const onSelect = (_event, value) => {
    const [run, metric] = value;
    dispatch(toggleSelectedMetric(run, metric));
    dispatch(fetchGraphData(run, metric));
    dispatch(fetchSummaryData(run, metric));
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
          id="checkbox-select"
          role="menu"
          isOpen={isOpen}
          selected={current_metrics}
          onSelect={onSelect}
          onOpenChange={(isOpen) => setIsOpen(isOpen)}
          toggle={toggle1}
        >
          <SelectList>
            {getMetricsData(item.id)[0]?.metrics.map((metric) => (
              <SelectOption
                key={metric}
                isSelected={current_metrics.includes(metric)}
                hasCheckbox
                value={[item.id, metric]}
              >
                {metric}
              </SelectOption>
            ))}
          </SelectList>
        </Select>
      ) : (
        <Skeleton width="33%" screenreaderText="Loaded 33% of content" />
      )}
    </>
  );
};

MetricsSelect.propTypes = {
  item: PropTypes.object,
};
export default MetricsSelect;
