import { Button, Popover } from "@patternfly/react-core";
import { Table, Tbody, Td, Th, Thead, Tr } from "@patternfly/react-table";
import { uid } from "@/utils/helper.js";
import { useSelector } from "react-redux";

const VersionWidget = () => {
  const { aggregatorVersion } = useSelector((state) => state.header);
  console.log(`VERSION: ${aggregatorVersion}`);
  return (
    <div key={uid()} className="version-wrapper">
      <Popover
        hasAutoWidth
        triggerAction="click"
        aria-label="Version popover"
        headerContent={<b>Version</b>}
        appendTo={() => document.body}
        hasNoPadding
        position="auto"
        bodyContent={
          <div className="mini-metadata">
            <Table
              variant="compact"
              hasNoInset
              className="box"
              key={uid()}
              aria-label="version-info"
              isStriped
            >
              <Tbody>
                <Tr>
                  <Td>SHA</Td>
                  <Td>{aggregatorVersion?.sha}</Td>
                </Tr>
                <Tr>
                  <Td>BRANCH</Td>
                  <Td>{aggregatorVersion?.branch}</Td>
                </Tr>
                <Tr>
                  <Td>DATE</Td>
                  <Td>{new Date(aggregatorVersion.date).toLocaleString()}</Td>
                </Tr>
                {aggregatorVersion?.changes?.length && (
                  <Tr>
                    <Td rowSpan={2}>
                      <Table
                        variant="compact"
                        hasNoInset
                        aria-label="version-change"
                        isStriped
                      >
                        <Thead>
                          <Tr>
                            <Th>SHA</Th>
                            <Th>AUTHOR</Th>
                            <Th>DATE</Th>
                            <Th>TITLE</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {aggregatorVersion.changes.map((change) => (
                            <>
                              <Tr>
                                <Td>{change.sha}</Td>
                                <Td>{change.author}</Td>
                                <Td>
                                  {new Date(change.date).toLocaleString()}
                                </Td>
                                <Td>{change.title}</Td>
                              </Tr>
                            </>
                          ))}
                        </Tbody>
                      </Table>
                    </Td>
                  </Tr>
                )}
              </Tbody>
            </Table>
          </div>
        }
      >
        <Button>
          Version {aggregatorVersion?.display_version || "version unknown"}
        </Button>
      </Popover>
    </div>
  );
};

export default VersionWidget;
