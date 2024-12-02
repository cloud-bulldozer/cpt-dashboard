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

const MetricsTab = (props) => {
  const [expanded, setExpanded] = useState("metrics-toggle");
  const { summary } = props;
  const onToggle = (id) => {
    if (id === expanded) {
      setExpanded("");
    } else {
      setExpanded(id);
    }
  };
  const removeStatusFilter = () => {
    if (
      Array.isArray(props.appliedFilters["jobStatus"]) &&
      props.appliedFilters["jobStatus"].length > 0
    ) {
      props.appliedFilters["jobStatus"].forEach((element) => {
        props.updateSelectedFilter("jobStatus", element, true);
        removeAppliedFilters(
          "jobStatus",
          element,
          props.navigation,
          props.type
        );
      });
    }
  };
  const applyStatusFilter = (value) => {
    props.updateSelectedFilter("jobStatus", value, true);
    setAppliedFilters(props.navigation, props.type);
  };
  const applyOtherFilter = () => {
    removeStatusFilter();
    setOtherSummaryFilter(props.type);
  };
  return (
    <Accordion togglePosition="start">
      <AccordionItem>
        <AccordionToggle
          onClick={() => {
            onToggle("metrics-toggle");
          }}
          isExpanded={expanded === "metrics-toggle"}
          id="metrics-toggle"
        >
          Summary
        </AccordionToggle>
        <AccordionContent
          id="metrics-toggle"
          isHidden={expanded !== "metrics-toggle"}
        >
          <MetricCard
            title={"No. of Jobs"}
            clickHandler={removeStatusFilter}
            footer={summary?.total}
          />
          <MetricCard
            title={"Success"}
            clickHandler={applyStatusFilter}
            footer={summary?.successCount}
          />
          <MetricCard
            title={"Failure"}
            clickHandler={applyStatusFilter}
            footer={summary?.failureCount}
          />
          <MetricCard
            title={"Others"}
            footer={summary?.othersCount}
            clickHandler={applyOtherFilter}
          />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
MetricsTab.propTypes = {
  totalItems: PropTypes.number,
  summary: PropTypes.object,
  type: PropTypes.string,
  updateSelectedFilter: PropTypes.func,
  navigation: PropTypes.func,
  appliedFilters: PropTypes.object,
};
export default MetricsTab;
