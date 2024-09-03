import "./index.less";

import { ExpandableRowContent, Tbody, Td, Tr } from "@patternfly/react-table";

import RowContent from "@/components/molecules/ExpandedRow";
import TableCell from "@/components/atoms/TableCell";
import { uid } from "@/utils/helper.js";

const TableRows = (props) => {
  const { rows, columns, addExpansion } = props;

  return (
    rows?.length > 0 &&
    rows.map((item, rowIndex) => {
      return addExpansion ? (
        <Tbody isExpanded={props?.isRunExpanded(item)} key={uid()}>
          <Tr>
            <Td
              expand={{
                rowIndex,
                isExpanded: props?.isRunExpanded(item),
                onToggle: () =>
                  props?.setRunExpanded(item, !props?.isRunExpanded(item)),
                expandId: `expandable-row${uid()}`,
              }}
            />

            {columns.map((col) => (
              <TableCell key={uid()} col={col} item={item} />
            ))}
          </Tr>

          <Tr isExpanded={props?.isRunExpanded(item)}>
            <Td colSpan={8}>
              <ExpandableRowContent>
                <RowContent
                  key={uid()}
                  item={item}
                  graphData={props.graphData}
                  type={props.type}
                />
              </ExpandableRowContent>
            </Td>
          </Tr>
        </Tbody>
      ) : (
        <Tr>
          {columns.map((col) => (
            <TableCell key={uid()} col={col} item={item} />
          ))}
        </Tr>
      );
    })
  );
};

export default TableRows;
