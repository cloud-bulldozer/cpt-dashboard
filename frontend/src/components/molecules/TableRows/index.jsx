import TableCell from "../../atoms/TableCell";
import { Tr } from "@patternfly/react-table";
import { uid } from "@/utils/helper.js";

const TableRows = (props) => {
  const { rows, columns } = props;
  return (
    rows?.length > 0 &&
    rows.map((item) => (
      <Tr key={uid()}>
        {columns.map((col) => (
          <TableCell key={uid()} col={col} item={item} />
        ))}
      </Tr>
    ))
  );
};

export default TableRows;
