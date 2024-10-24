import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
  Card,
  CardBody,
} from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import ILabGraph from "./ILabGraph";
import MetaRow from "./MetaRow";
import MetricsSelect from "./MetricsDropdown";
import PropTypes from "prop-types";
import { setMetaRowExpanded } from "@/actions/ilabActions";
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
      <AccordionItem>
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
                {item.iterations.length > 1 && (
                  <AccordionItem>
                    <AccordionToggle
                      onClick={() => {
                        onToggle(`iterations-toggle-${item.id}`);
                      }}
                      isExpanded={metaRowExpanded.includes(
                        `iterations-toggle-${item.id}`
                      )}
                      id={`iterations-toggle-${item.id}`}
                    >
                      {`Unique parameters for ${item.iterations.length} Iterations`}
                    </AccordionToggle>
                    <AccordionContent
                      id={`iterations-${item.id}`}
                      isHidden={
                        !metaRowExpanded.includes(
                          `iterations-toggle-${item.id}`
                        )
                      }
                    >
                      {item.iterations.map((i) => (
                        <MetaRow
                          key={uid()}
                          heading={`Iteration ${i.iteration} Parameters`}
                          metadata={Object.entries(i.params).filter(
                            (i) => !(i[0] in item.params)
                          )}
                        />
                      ))}
                    </AccordionContent>
                  </AccordionItem>
                )}
              </CardBody>
            </Card>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem>
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
          <MetricsSelect item={item} />
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
