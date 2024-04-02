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

// const TableCell = (props) => {
//   const { col, item } = props;
//   return (
//     <Td dataLabel={col.name} key={uid()}>
//       {col.name === "Status" ? (
//         item[col.value] === "success" ? (
//           <Label color="green" icon={<CheckCircleIcon />}>
//             Success
//           </Label>
//         ) : (
//           <Label color="red" icon={<ExclamationCircleIcon />}>
//             Failure
//           </Label>
//         )
//       ) : col.name === "Start Date" || col.name === "End Date" ? (
//         formatDateTime(item[col.value])
//       ) : col.name === "Build URL" ? (
//         <Button
//           variant="link"
//           component="a"
//           href={item[col.value]}
//           target="_blank"
//           icon={<ExternalLinkSquareAltIcon />}
//           iconPosition="end"
//         >
//           Job
//         </Button>
//       ) : (
//         item[col.value]
//       )}
//     </Td>
//   );
// };
export default TableRows;
