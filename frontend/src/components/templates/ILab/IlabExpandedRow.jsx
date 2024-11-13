import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
  Stack,
  StackItem,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import ILabGraph from "./ILabGraph";
import ILabSummary from "./ILabSummary";
import MetricsSelect from "./MetricsDropdown";
import PropTypes from "prop-types";
import { setMetaRowExpanded } from "@/actions/ilabActions";
import ILabMetadata from "./ILabMetadata";
import { uid } from "@/utils/helper";

const IlabRowContent = (props) => {
  const { item } = props;
  const dispatch = useDispatch();
  const { metaRowExpanded } = useSelector((state) => state.ilab);

  const onToggle = (id) => {
    const index = metaRowExpanded.indexOf(id);
    const newExpanded =
      index >= 0
        ? [
            ...metaRowExpanded.slice(0, index),
            ...metaRowExpanded.slice(index + 1, metaRowExpanded.length),
          ]
        : [...metaRowExpanded, id];

    dispatch(setMetaRowExpanded(newExpanded));
  };
  return (
    <Accordion asDefinitionList={false} togglePosition="start">
      <AccordionItem key={uid()}>
        <AccordionToggle
          onClick={() => {
            onToggle(`metadata-toggle-${item.id}`);
          }}
          isExpanded={metaRowExpanded.includes(`metadata-toggle-${item.id}`)}
          id={`metadata-toggle-${item.id}`}
        >
          Metadata
        </AccordionToggle>

        <AccordionContent
          id={`metadata-${item.id}`}
          isHidden={!metaRowExpanded.includes(`metadata-toggle-${item.id}`)}
        >
          <ILabMetadata item={item} />
        </AccordionContent>
      </AccordionItem>
      <AccordionItem key={uid()}>
        <AccordionToggle
          onClick={() => {
            onToggle(`graph-toggle-${item.id}`);
          }}
          isExpanded={metaRowExpanded.includes(`graph-toggle-${item.id}`)}
          id={`graph-toggle-${item.id}`}
        >
          Metrics & Graph
        </AccordionToggle>
        <AccordionContent
          id={`graph-${item.id}`}
          isHidden={!metaRowExpanded.includes(`graph-toggle-${item.id}`)}
        >
          <div>Metrics:</div>
          <MetricsSelect ids={[item.id]} />
          <Stack>
            <StackItem key={uid()} id="summary" className="summary-card">
              <ILabSummary ids={[item.id]} />
            </StackItem>
            <StackItem key={uid()} id="graph" className="graph-card">
              <ILabGraph item={item} />
            </StackItem>
          </Stack>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
IlabRowContent.propTypes = {
  item: PropTypes.object,
};
export default IlabRowContent;
