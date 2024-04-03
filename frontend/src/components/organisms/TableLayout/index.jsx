import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import TableRows from "../../molecules/TableRows";
import { uid } from "@/utils/helper.js";

const TableLayout = (props) => {
  const {
    tableData,
    tableColumns,
    activeSortIndex,
    activeSortDir,
    setActiveSortIndex,
    setActiveSortDir,
  } = props;

  const getSortParams = (columnIndex) => ({
    sortBy: {
      index: activeSortIndex,
      direction: activeSortDir,
      defaultDirection: "asc",
    },
    onSort: (_event, index, direction) => {
      setActiveSortIndex(index);
      setActiveSortDir(direction);
    },
    columnIndex,
  });

  return (
    <Table isStriped>
      <Thead>
        <Tr>
          {tableColumns?.length > 0 &&
            tableColumns.map((col, idx) => (
              <Th key={uid()} sort={getSortParams(idx)}>
                {col.name}
              </Th>
            ))}
        </Tr>
      </Thead>
      <Tbody>
        <TableRows rows={tableData} columns={tableColumns} />
      </Tbody>
    </Table>
  );
};

export default TableLayout;
