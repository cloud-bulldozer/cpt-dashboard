import { Button, Tooltip } from "@patternfly/react-core";

import { ColumnsIcon } from "@patternfly/react-icons";

const TableColumnIcon = () => {
  return (
    <Tooltip aria="none" aria-live="polite" content={"Manage columns"}>
      <Button variant="control" aria-label="Manage columns">
        <ColumnsIcon />
      </Button>
    </Tooltip>
  );
};
export default TableColumnIcon;
