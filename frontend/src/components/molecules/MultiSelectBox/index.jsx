import {
  Chip,
  ChipGroup,
  MenuToggle,
  Select,
  SelectList,
  SelectOption,
  TextInputGroup,
  TextInputGroupMain,
} from "@patternfly/react-core";

import PropTypes from "prop-types";
import { useState } from "react";

const MultiSelectBox = (props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const onSelect = (value) => {
    setIsDirty(true);
    props.onChange(props.currCategory, value);
  };

  const onToggleClick = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
    if (isDirty) {
      props.applyMethod();
    }
    setIsDirty(false);
  };
  const toggle = (toggleRef) => {
    return (
      <MenuToggle
        variant="typeahead"
        aria-label="Multi typeahead menu toggle"
        onClick={onToggleClick}
        innerRef={toggleRef}
        isExpanded={isOpen}
        style={{
          width: props.width,
          height: "36px",
        }}
      >
        {Array.isArray(props.selected.value) &&
        props.selected.value.length > 0 ? (
          <TextInputGroup>
            <TextInputGroupMain>
              <ChipGroup numChips={2}>
                {props.selected.value.map((selection, index) => (
                  <Chip
                    key={index}
                    isReadOnly={true}
                    //   onClick={(ev) => {
                    //     ev.stopPropagation();
                    //     onSelect(selection);
                    //   }}
                  >
                    {selection}
                  </Chip>
                ))}
              </ChipGroup>
            </TextInputGroupMain>
          </TextInputGroup>
        ) : (
          <TextInputGroup>
            <TextInputGroupMain value={"Select a value"} />
          </TextInputGroup>
        )}
      </MenuToggle>
    );
  };
  const createItemId = (value) =>
    `select-multi-typeahead-${value?.toString()?.replace(" ", "-")}`;
  return (
    <>
      <Select
        id="multi-typeahead-select"
        isOpen={isOpen}
        selected={props.selected?.value}
        onSelect={(_event, selection) => onSelect(selection)}
        onOpenChange={(isOpen) => {
          !isOpen && closeMenu();
        }}
        toggle={toggle}
        shouldFocusFirstItemOnOpen={false}
      >
        <SelectList isAriaMultiselectable id="select-multi-typeahead-listbox">
          {props.options.map((option) => (
            <SelectOption
              key={option.value}
              className={option.className}
              id={createItemId(option.value)}
              {...option}
              ref={null}
            >
              {option.value}
            </SelectOption>
          ))}
        </SelectList>
      </Select>
    </>
  );
};

MultiSelectBox.propTypes = {
  options: PropTypes.array,
  onChange: PropTypes.func,
  selected: PropTypes.object,
  applyMethod: PropTypes.func,
  currCategory: PropTypes.string,
  width: PropTypes.string,
};
export default MultiSelectBox;
