import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionToggle,
  Split,
  SplitItem,
} from "@patternfly/react-core";
import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import { useDispatch, useSelector } from "react-redux";

import MetaRow from "./MetaRow";
import PropType from "prop-types";
import { setMetaRowExpanded } from "@/actions/ilabActions";
import { uid } from "@/utils/helper";

const ILabMetadata = (props) => {
  const { item } = props;
  const { metaRowExpanded } = useSelector((state) => state.ilab);
  const dispatch = useDispatch();

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
    <Split className="metadata-wrapper" hasGutter>
      <SplitItem className="metadata-card" span={4}>
        <MetaRow
          key={uid()}
          heading={"Fields"}
          metadata={[
            ["benchmark", item.benchmark],
            ["name", item.name],
            ["email", item.email],
            ["source", item.source],
            ["start_date", new Date(item.begin).toLocaleString()],
            ["end_date", new Date(item.end).toLocaleString()],
            ["status", item.status],
          ]}
        />
      </SplitItem>
      <SplitItem className="metadata-card" span={4}>
        <MetaRow
          key={uid()}
          heading={"Tags"}
          metadata={Object.entries(item.tags)}
        />
      </SplitItem>
      <SplitItem className="metadata-card" span={4}>
        <MetaRow
          key={uid()}
          heading={"Common Parameters"}
          metadata={Object.entries(item.params)}
        />
        {item.iterations.length > 1 && (
          <Accordion asDefinitionList={false} togglePosition="start">
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
                  !metaRowExpanded.includes(`iterations-toggle-${item.id}`)
                }
              >
                <Table
                  variant="compact"
                  hasNoInset
                  className="box"
                  key={uid()}
                  aria-label="metadata-table"
                  isStriped
                >
                  <Thead>
                    <Tr>
                      <Th>Iteration</Th>
                      <Th>Parameter</Th>
                      <Th>Value</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {item.iterations.map((i) =>
                      Object.entries(i.params)
                        .filter((p) => !(p[0] in item.params))
                        .map((p) => (
                          <Tr key={uid()}>
                            <Td>{i.iteration}</Td>
                            <Td>{p[0]}</Td>
                            <Td>{p[1]}</Td>
                          </Tr>
                        ))
                    )}
                  </Tbody>
                </Table>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
      </SplitItem>
    </Split>
  );
};

ILabMetadata.propTypes = {
  item: PropType.object,
};
export default ILabMetadata;
