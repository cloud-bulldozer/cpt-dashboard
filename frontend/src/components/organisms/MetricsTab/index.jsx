import "./index.less";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
} from "@patternfly/react-core";

import MetricCard from "@/components/molecules/MetricCard";
import PropTypes from "prop-types";
import { useState } from "react";

const MetricsTab = (props) => {
  const [expanded, setExpanded] = useState("metrics-toggle");
  const { totalItems, summary } = props;
  const onToggle = (id) => {
    if (id === expanded) {
      setExpanded("");
    } else {
      setExpanded(id);
    }
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
            clickHandler={props.removeStatusFilter}
            footer={totalItems}
          />
          <MetricCard
            title={"Success"}
            clickHandler={props.applyStatusFilter}
            footer={summary?.successCount}
          />
          <MetricCard
            title={"Failure"}
            clickHandler={props.applyStatusFilter}
            footer={summary?.failureCount}
          />
          <MetricCard
            title={"Others"}
            footer={summary?.othersCount}
            clickHandler={props.applyOtherFilter}
          />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
MetricsTab.propTypes = {
  totalItems: PropTypes.number,
  summary: PropTypes.object,
  removeStatusFilter: PropTypes.func,
  applyStatusFilter: PropTypes.func,
  applyOtherFilter: PropTypes.func,
};
export default MetricsTab;
