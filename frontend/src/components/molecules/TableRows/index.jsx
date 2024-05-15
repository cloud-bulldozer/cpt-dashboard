import { ExpandableRowContent, Td, Tr } from "@patternfly/react-table";

import TableCell from "../../atoms/TableCell";
import { uid } from "@/utils/helper.js";

const TableRows = (props) => {
  const { rows, columns, addExpansion } = props;
  const details = true;
  const setRepoExpanded = () => {
    console.log("hey");
  };
  return (
    rows?.length > 0 &&
    rows.map((item, rowIndex) => (
      <>
        <Tr key={uid()}>
          {addExpansion && (
            <Td
              expand={
                details
                  ? {
                      rowIndex,
                      isExpanded: true,
                      onToggle: () => setRepoExpanded(),
                      expandId: "expandable-row",
                    }
                  : undefined
              }
            />
          )}

          {columns.map((col) => (
            <TableCell key={uid()} col={col} item={item} />
          ))}
        </Tr>
        {addExpansion && (
          <Tr isExpanded={false}>
            <Td colSpan={8}>
              <ExpandableRowContent>
                Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit
                dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum
                sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem
                ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor.
                Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit
                dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum
                sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem
                ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor.
                Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit
                dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum
                sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor. Lorem
                ipsum sit dolor. Lorem ipsum sit dolor. Lorem ipsum sit dolor.
              </ExpandableRowContent>
            </Td>
          </Tr>
        )}
      </>
    ))
  );
};

export default TableRows;
