import "./index.less";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
} from "@patternfly/react-core";
import {
  removeAppliedFilters,
  setAppliedFilters,
  setOtherSummaryFilter,
} from "@/actions/filterActions";

import MetricCard from "@/components/molecules/MetricCard";
import PropTypes from "prop-types";
import { useState } from "react";

const titleMap = {
  total: "No. of jobs",
  successCount: "Success",
  failureCount: "Failure",
  othersCount: "Others",
};

const MetricsTab = (props) => {
  const [expanded, setExpanded] = useState("metrics-toggle");
  const { updateSelectedFilter, navigation, type, appliedFilters, summary } =
    props;

  const onToggle = (id) => {
    if (id === expanded) {
      setExpanded("");
    } else {
      setExpanded(id);
    }
  };
  const removeStatusFilter = () => {
    const statusFilters = appliedFilters["jobStatus"];

    if (Array.isArray(statusFilters) && statusFilters.length > 0) {
      statusFilters.forEach((element) => {
        updateSelectedFilter("jobStatus", element, true);
        removeAppliedFilters("jobStatus", element, navigation, type);
      });
    }
  };
  const applyStatusFilter = (value) => {
    updateSelectedFilter("jobStatus", value, true);
    setAppliedFilters(navigation, type);
  };
  const applyOtherFilter = () => {
    removeStatusFilter();
    setOtherSummaryFilter(type);
  };
  const filterFuncMap = {
    total: removeStatusFilter,
    successCount: () => applyStatusFilter("success"),
    failureCount: () => applyStatusFilter("failure"),
    othersCount: applyOtherFilter,
  };
  return (
    <Accordion togglePosition="start">
      {summary && Object.keys(summary).length > 0 && (
        <AccordionItem>
          <AccordionToggle
            onClick={() => {
              onToggle("metrics-toggle");
            }}
            isExpanded={expanded === "metrics-toggle"}
            id="metrics-toggle"
            ouiaId="summary_toggle"
          >
            Summary
          </AccordionToggle>
          <AccordionContent
            id="metrics-toggle"
            className="metrics-toggle-content"
            isHidden={expanded !== "metrics-toggle"}
          >
            {Object.entries(summary).map(([key, value]) => (
              <MetricCard
                key={key}
                title={titleMap[key]}
                clickHandler={() => filterFuncMap[key]?.()}
                footer={value}
              />
            ))}
          </AccordionContent>
        </AccordionItem>
      )}
    </Accordion>
  );
};
MetricsTab.propTypes = {
  summary: PropTypes.object,
  type: PropTypes.string,
  updateSelectedFilter: PropTypes.func,
  navigation: PropTypes.func,
  appliedFilters: PropTypes.object,
};
export default MetricsTab;
