import {
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@patternfly/react-icons";

import { Label } from "@patternfly/react-core";
import Proptype from "prop-types";

const StatusCell = (props) => {
  return props.value?.toLowerCase() === "pass" ? (
    <Label color="green" icon={<CheckCircleIcon />}>
      Success
    </Label>
  ) : (
    <Label color="red" icon={<ExclamationCircleIcon />}>
      Failure
    </Label>
  );
};
StatusCell.propTypes = {
  value: Proptype.string,
};

export default StatusCell;
