import {
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
} from "@patternfly/react-core";

import PropTypes from "prop-types";
import { useState } from "react";

const SelectBox = (props) => {
  const [isOpen, setIsOpen] = useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };
  const onSelect = (_event, value) => {
    setIsOpen(false);
    props.onChange(_event, value);
  };
  const toggle = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      icon={props?.icon}
      onClick={onToggleClick}
      isExpanded={isOpen}
      style={{
        width: props.width,
      }}
    >
      {props.selected}
    </MenuToggle>
  );
  return (
    <>
      <Select
        className="select-box"
        isOpen={isOpen}
        selected={props.onChange}
        onSelect={onSelect}
        onOpenChange={(isOpen) => setIsOpen(isOpen)}
        toggle={toggle}
        shouldFocusToggleOnSelect
      >
        <SelectList>
          {props.options.map((option) => (
            <SelectOption value={option.name} key={option.value}>
              {option.name}
            </SelectOption>
          ))}
        </SelectList>
      </Select>
    </>
  );
};

SelectBox.propTypes = {
  options: PropTypes.array,
  onChange: PropTypes.func,
  selected: PropTypes.string,
  width: PropTypes.string,
  icon: PropTypes.any,
};
export default SelectBox;
