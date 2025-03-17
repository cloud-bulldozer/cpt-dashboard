import {
  Badge,
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
  Skeleton,
} from "@patternfly/react-core";
import {
  retrieveGraphAndSummary,
  toggleSelectedMetric,
} from "@/actions/ilabActions";
import { useCallback, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import PropTypes from "prop-types";

const MetricsSelect = (props) => {
  const metrics = useSelector((state) => state.ilab.metrics);
  const metrics_selected = useSelector((state) => state.ilab.metrics_selected);
  const { ids, selectedMetric, setSelectedMetric } = props;
  const comparisonSwitch = useSelector((state) => state.ilab.comparisonSwitch);

  /* Metrics select */
  const [isOpen, setIsOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [currentSelections, setCurrentSelections] = useState(
    comparisonSwitch ? selectedMetric || [] : metrics_selected || []
  );

  const dispatch = useDispatch();

  const onToggleClick = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const toggle = useCallback(
    (toggleRef) => (
      <MenuToggle
        ref={toggleRef}
        onClick={onToggleClick}
        isExpanded={isOpen}
        badge={<Badge isRead>{`${currentSelections.length} selected`}</Badge>}
      >
        Additional metrics
      </MenuToggle>
    ),
    [isOpen, onToggleClick, currentSelections?.length]
  );

  const onSelect = (_event, metric) => {
    setIsDirty(true);
    setCurrentSelections((prevSelections) =>
      prevSelections.includes(metric)
        ? prevSelections.filter((m) => m !== metric)
        : [...prevSelections, metric]
    );
  };

  const closeMenu = () => {
    if (ids.length > 0 && isDirty) {
      // If we're closing, fetch data
      // setSelectedMetric is for expanded row else it is comparison view
      if (setSelectedMetric) {
        setSelectedMetric(currentSelections);
      } else {
        dispatch(toggleSelectedMetric(currentSelections));
      }
      dispatch(retrieveGraphAndSummary(ids));
    }
    setIsDirty(false);
    setIsOpen(false);
  };
  const hasAllMetricsData = (runs) => {
    const hasData = Boolean(
      metrics?.filter((i) => runs.includes(i.uid)).length === runs.length
    );
    return hasData;
  };

  const all_metrics = useMemo(() => {
    const collector = new Set();
    metrics
      .filter((a) => ids.includes(a.uid))
      .forEach((a) => a.metrics?.forEach((k) => collector.add(k)));
    return [...collector].sort();
  }, [metrics, ids]);

  const createItemId = (value) => `select-multi-${value.replace(" ", "-")}`;
  /* Metrics select */
  return (
    <>
      {hasAllMetricsData(ids) ? (
        <Select
          id="checkbox-select"
          role="menu"
          isOpen={isOpen}
          selected={currentSelections}
          onSelect={onSelect}
          onOpenChange={(isOpen) => {
            !isOpen && closeMenu();
          }}
          toggle={toggle}
        >
          <SelectList>
            {all_metrics.map((metric) => (
              <SelectOption
                key={metric}
                id={createItemId(metric)}
                isSelected={currentSelections.includes(metric)}
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
  selectedMetric: PropTypes.array,
  setSelectedMetric: PropTypes.func,
};
export default MetricsSelect;
