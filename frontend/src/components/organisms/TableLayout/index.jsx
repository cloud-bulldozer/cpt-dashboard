import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import TableRows from "../../molecules/TableRows";
import { uid } from "@/utils/helper.js";

const TableLayout = (props) => {
  const { tableData, tableColumns } = props;

  const columns = tableColumns?.map((item) => item.value);
  return (
    <Table isStriped>
      <Thead>
        <Tr>
          {tableColumns?.length > 0 &&
            tableColumns.map((col) => <Th key={uid()}>{col.name}</Th>)}
        </Tr>
      </Thead>
      <Tbody>
        <TableRows rows={tableData} columns={tableColumns} />
      </Tbody>
    </Table>
  );
};

export default TableLayout;
