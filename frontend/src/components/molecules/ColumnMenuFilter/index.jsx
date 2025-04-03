import "./index.less";

import {
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
} from "@patternfly/react-core";
import React, { useMemo } from "react";

import PropTypes from "prop-types";
import TableColumnIcon from "@/components/atoms/TableColumnIcon";
import { uid } from "@/utils/helper";
import { useSelector } from "react-redux";

const ColumnMenuFilter = (props) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const { tableFilters, tableColumns } = useSelector(
    (state) => state[props.type]
  );

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const activeTableColumns = useMemo(
    () => tableColumns.map((col) => col.value),
    [tableColumns]
  );

  const onSelect = (_event, value) => {
    if (activeTableColumns.includes(value)) {
      props.setColumns(value, false);
    } else {
      props.setColumns(value, true);
    }
  };
  const toggle = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      variant="plain"
      onClick={onToggleClick}
      isExpanded={isOpen}
      className="column-icon-menu"
    >
      <TableColumnIcon />
    </MenuToggle>
  );
  return (
    <Select
      role="menu"
      id="checkbox-select"
      isOpen={isOpen}
      selected={activeTableColumns}
      onSelect={onSelect}
      onOpenChange={(nextOpen) => setIsOpen(nextOpen)}
      toggle={toggle}
    >
      <SelectList>
        {tableFilters.map((filter) => (
          <SelectOption
            key={uid()}
            hasCheckbox
            value={filter.value}
            isSelected={activeTableColumns.includes(filter.value)}
          >
            {filter.name}
          </SelectOption>
        ))}
      </SelectList>
    </Select>
  );
};

ColumnMenuFilter.propTypes = {
  type: PropTypes.string,
  setColumns: PropTypes.func,
};

export default ColumnMenuFilter;
