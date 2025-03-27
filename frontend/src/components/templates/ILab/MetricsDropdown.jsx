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
  fetchMultiGraphData,
  fetchSummaryData,
  handleSummaryData,
  toggleSelectedMetric,
} from "@/actions/ilabActions";
import { useDispatch, useSelector } from "react-redux";

import PropTypes from "prop-types";
import { useState } from "react";

const MetricsSelect = (props) => {
  const { metrics, metrics_selected } = useSelector((state) => state.ilab);
  const { ids } = props;

  /* Metrics select */
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch();

  const toggle1 = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      onClick={onToggleClick}
      isExpanded={isOpen}
      badge={<Badge isRead>{`${metrics_selected.length} selected`}</Badge>}
    >
      Additional metrics
    </MenuToggle>
  );

  const onToggleClick = async () => {
    setIsOpen(!isOpen);
  };
  const onSelect = (_event, metric) => {
    dispatch(toggleSelectedMetric(metric));
  };

  const onOpenChange = async (nextOpen) => {
    if (!nextOpen && ids.length > 0) {
      // If we're closing, fetch data

      if (ids.length === 1) {
        await Promise.all([
          await dispatch(fetchGraphData(ids[0])),
          await dispatch(fetchSummaryData(ids[0])),
        ]);
      } else {
        await Promise.all([
          await dispatch(fetchMultiGraphData(ids)),
          await dispatch(handleSummaryData(ids)),
        ]);
      }
    }
    setIsOpen(nextOpen);
  };

  const getMetricsData = (id) => {
    const data = metrics?.filter((a) => a.uid === id);
    return data?.metrics;
  };
  const hasAllMetricsData = (runs) => {
    const hasData = Boolean(
      metrics?.filter((i) => runs.includes(i.uid)).length === runs.length
    );
    return hasData;
  };

  // de-dup a "set" using object keys
  var collector = {};
  if (hasAllMetricsData(ids)) {
    const datas = metrics.filter((a) => ids.includes(a.uid));
    if (datas) {
      datas.forEach((a) => {
        if (a.metrics) {
          a.metrics.forEach((k) => (collector[k] = true));
        }
      });
    }
  }
  const all_metrics = Object.keys(collector).sort();

  /* Metrics select */
  return (
    <>
      {hasAllMetricsData(ids) ? (
        <Select
          id="checkbox-select"
          role="menu"
          isOpen={isOpen}
          selected={metrics_selected}
          onSelect={onSelect}
          onOpenChange={onOpenChange}
          toggle={toggle1}
        >
          <SelectList>
            {all_metrics.map((metric) => (
              <SelectOption
                key={metric}
                isSelected={metrics_selected.includes(metric)}
                hasCheckbox
                value={metric}
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
  ids: PropTypes.array,
};
export default MetricsSelect;
