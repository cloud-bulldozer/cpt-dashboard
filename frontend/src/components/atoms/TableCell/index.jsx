import { Button, Label } from "@patternfly/react-core";
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExternalLinkSquareAltIcon,
  ExclamationTriangleIcon,
} from "@patternfly/react-icons";
import { formatDateTime, uid } from "@/utils/helper.js";

import PropTypes from "prop-types";
import { Td } from "@patternfly/react-table";
import { SUCCESS, FAILURE } from "@/assets/constants/jobStatusConstants";

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
  return item[col.value]?.toLowerCase() === SUCCESS ? (
    <Label
      color="green"
      icon={<CheckCircleIcon data-ouia-component-id="check_circle_icon" />}
    >
      Success
    </Label>
  ) : item[col.value]?.toLowerCase() === FAILURE ? (
    <Label
      color="red"
      icon={
        <ExclamationCircleIcon data-ouia-component-id="exclamation_circle_icon" />
      }
    >
      Failure
    </Label>
  ) : (
    <Label
      color="orange"
      icon={
        <ExclamationTriangleIcon data-ouia-component-id="exclamation_triangle_icon" />
      }
    >
      Others
    </Label>
  );
};

const BuildURLCell = (props) => (
  <Button
    variant="link"
    component="a"
    href={props.item[props.col.value]}
    target="_blank"
    icon={
      <ExternalLinkSquareAltIcon data-ouia-component-id="external_link_square_icon" />
    }
    iconPosition="end"
  >
    Job
  </Button>
);

StatusCell.propTypes = {
  item: PropTypes.object,
  col: PropTypes.object,
};
TableCell.propTypes = {
  item: PropTypes.object,
  col: PropTypes.object,
};
BuildURLCell.propTypes = {
  item: PropTypes.object,
  col: PropTypes.object,
};
export default TableCell;
