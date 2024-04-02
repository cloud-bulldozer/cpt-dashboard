import { Button, Label } from "@patternfly/react-core";
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExternalLinkSquareAltIcon,
} from "@patternfly/react-icons";
import { formatDateTime, uid } from "@/utils/helper.js";

import { Td } from "@patternfly/react-table";

const TableCell = (props) => {
  const { col, item } = props;
  return (
    <Td dataLabel={col.name} key={uid()}>
      {col.value === "jobStatus" ? (
        <StatusCell item={item} col={col} />
      ) : col.value === "startDate" || col.value === "endDate" ? (
        formatDateTime(item[col.value])
      ) : col.value === "buildUrl" ? (
        <BuildURLCell item={item} col={col} />
      ) : (
        item[col.value]
      )}
    </Td>
  );
};

const StatusCell = (props) => {
  const { item, col } = props;
  return item[col.value] === "success" ? (
    <Label color="green" icon={<CheckCircleIcon />}>
      Success
    </Label>
  ) : (
    <Label color="red" icon={<ExclamationCircleIcon />}>
      Failure
    </Label>
  );
};

const BuildURLCell = (props) => (
  <Button
    variant="link"
    component="a"
    href={props.item[props.col.value]}
    target="_blank"
    icon={<ExternalLinkSquareAltIcon />}
    iconPosition="end"
  >
    Job
  </Button>
);

export default TableCell;
