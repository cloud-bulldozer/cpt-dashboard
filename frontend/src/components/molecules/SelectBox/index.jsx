import {
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
} from "@patternfly/react-core";

import PropTypes from "prop-types";
import { useState } from "react";

const SelectBox = (props) => {
  const { options, type, selected } = props;
  const [isOpen, setIsOpen] = useState(false);

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };
  const onSelect = (_event, value) => {
    setIsOpen(false);
    props.onChange(_event, value);
  };
  const renderOptions = () => {
    switch (type) {
      case "ilab":
        return (
          <SelectList>
            {options.map(({ groupLabel }) => (
              <SelectOption value={groupLabel} key={groupLabel}>
                {groupLabel}
              </SelectOption>
            ))}
          </SelectList>
        );
      case "ilab_subcategory":
        return (
          <SelectList>
            {options.map(({ key, name }) => (
              <SelectOption value={key} key={key}>
                {name}
              </SelectOption>
            ))}
          </SelectList>
        );
      case "ilab_type_filter":
        return (
          <SelectList>
            {options.map((option) => (
              <SelectOption value={option} key={option}>
                {option}
              </SelectOption>
            ))}
          </SelectList>
        );
      default:
        return (
          <SelectList>
            {options.map(({ key, name }) => (
              <SelectOption value={name} key={key}>
                {name}
              </SelectOption>
            ))}
          </SelectList>
        );
    }
  };

  const toggle = (toggleRef) => (
    <MenuToggle
      ref={toggleRef}
      icon={props?.icon}
      onClick={onToggleClick}
      isExpanded={isOpen}
      style={{
        width: props.width,
        height: "36px",
      }}
    >
      {selected}
    </MenuToggle>
  );
  return (
    <Select
      className="select-box"
      isOpen={isOpen}
      selected={selected}
      onSelect={onSelect}
      onOpenChange={setIsOpen}
      toggle={toggle}
      shouldFocusToggleOnSelect
    >
      {renderOptions()}
    </Select>
  );
};

SelectBox.propTypes = {
  options: PropTypes.array,
  onChange: PropTypes.func,
  selected: PropTypes.string,
  width: PropTypes.string,
  icon: PropTypes.any,
  type: PropTypes.string,
};
export default SelectBox;
