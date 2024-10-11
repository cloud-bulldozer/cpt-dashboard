import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
  Card,
  CardBody,
} from "@patternfly/react-core";

import ILabGraph from "./ILabGraph";
import MetaRow from "./MetaRow";
import MetricsSelect from "./MetricsDropdown";
import PropTypes from "prop-types";
import { uid } from "@/utils/helper";
import { useState } from "react";

const IlabRowContent = (props) => {
  const { item } = props;
  const [expanded, setAccExpanded] = useState(["bordered-toggle1"]);
  const onToggle = (id) => {
    const index = expanded.indexOf(id);
    const newExpanded =
      index >= 0
        ? [
            ...expanded.slice(0, index),
            ...expanded.slice(index + 1, expanded.length),
          ]
        : [...expanded, id];
    setAccExpanded(newExpanded);
  };

  return (
    <Accordion asDefinitionList={false} togglePosition="start">
      <AccordionItem>
        <AccordionToggle
          onClick={() => {
            onToggle("bordered-toggle1");
          }}
          isExpanded={expanded.includes("bordered-toggle1")}
          id="bordered-toggle1"
        >
          Metadata
        </AccordionToggle>

        <AccordionContent
          id="bordered-expand1"
          isHidden={!expanded.includes("bordered-toggle1")}
        >
          <div className="metadata-wrapper">
            <Card className="metadata-card" isCompact>
              <CardBody>
                <MetaRow
                  key={uid()}
                  heading={"Fields"}
                  metadata={[
                    ["benchmark", item.benchmark],
                    ["name", item.name],
                    ["email", item.email],
                    ["source", item.source],
                  ]}
                />
              </CardBody>
            </Card>
            <Card className="metadata-card" isCompact>
              <CardBody>
                <MetaRow
                  key={uid()}
                  heading={"Tags"}
                  metadata={Object.entries(item.tags)}
                />
              </CardBody>
            </Card>
            <Card className="metadata-card" isCompact>
              <CardBody>
                <MetaRow
                  key={uid()}
                  heading={"Common Parameters"}
                  metadata={Object.entries(item.params)}
                />
              </CardBody>
            </Card>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem>
        <AccordionToggle
          onClick={() => {
            onToggle("bordered-toggle2");
          }}
          isExpanded={expanded.includes("bordered-toggle2")}
          id="bordered-toggle2"
        >
          Metrics & Graph
        </AccordionToggle>
        <AccordionContent
          id="bordered-expand2"
          isHidden={!expanded.includes("bordered-toggle2")}
        >
          Metrics: <MetricsSelect item={item} />
          <div className="graph-card">
            <ILabGraph item={item} />
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
IlabRowContent.propTypes = {
  item: PropTypes.object,
};
export default IlabRowContent;
