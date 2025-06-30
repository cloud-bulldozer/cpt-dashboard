import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";

import {
  Button,
  Chip,
  ChipGroup,
  Switch,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";
import {
  removeAllFilters,
  setIlabCatFilters,
  setIlabSubCatFilters,
  setIlabTypeFilter,
} from "@/actions/ilabActions.js";
import { useDispatch, useSelector } from "react-redux";

import DatePicker from "react-date-picker";
import { FilterIcon } from "@patternfly/react-icons";
import PropTypes from "prop-types";
import SelectBox from "@/components/molecules/SelectBox";
import { formatDate } from "@/utils/helper";
import { removeIlabAppliedFilters } from "@/actions/ilabActions";
import { setDateFilter } from "@/actions/filterActions.js";
import { useNavigate } from "react-router-dom";

export const ILabFilters = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const {
    onSwitchChange,
    isSwitchChecked,
    start_date,
    end_date,
    navigation,
    type,
    filterData,
  } = props;
  const {
    subCategoryOptions,
    categoryFilterValue,
    subCategoryFilterValue,
    typeFilterOptions,
    typeFilterValue,
    appliedFilters,
  } = useSelector((state) => state.ilab);
  const startDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  const endDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  const onCategoryChange = (_event, value) => {
    dispatch(setIlabCatFilters(value));
  };
  const onSubCategoryChange = (_event, value) => {
    dispatch(setIlabSubCatFilters(value));
  };
  const onTypeFilterChange = (_event, value) => {
    dispatch(setIlabTypeFilter(value, navigate));
  };
  const deleteItem = (key, value) => {
    dispatch(removeIlabAppliedFilters(key, value, navigation));
  };
  return (
    <>
      {filterData.length > 0 && (
        <Toolbar id="filter-toolbar" ouiaId="data_table_filter">
          <ToolbarContent className="field-filter">
            <ToolbarItem style={{ marginInlineEnd: 0 }}>
              <SelectBox
                options={filterData}
                onChange={onCategoryChange}
                selected={categoryFilterValue}
                icon={<FilterIcon />}
                width={"200px"}
                type={"ilab"}
              />
            </ToolbarItem>
          </ToolbarContent>
          <ToolbarContent className="field-filter">
            <ToolbarItem style={{ marginInlineEnd: 0 }}>
              <SelectBox
                options={subCategoryOptions}
                onChange={onSubCategoryChange}
                selected={subCategoryFilterValue || "Select the value"}
                icon={<FilterIcon />}
                width={"300px"}
                type={"ilab_subcategory"}
              />
            </ToolbarItem>
          </ToolbarContent>
          {subCategoryFilterValue && (
            <ToolbarContent className="field-filter">
              <ToolbarItem style={{ marginInlineEnd: 0 }}>
                <SelectBox
                  options={typeFilterOptions}
                  onChange={onTypeFilterChange}
                  selected={typeFilterValue || "Select the value"}
                  icon={<FilterIcon />}
                  width={"300px"}
                  type={"ilab_type_filter"}
                />
              </ToolbarItem>
            </ToolbarContent>
          )}
          <ToolbarContent className="date-filter" ouiaId="date_filter">
            <ToolbarItem>
              <DatePicker
                onChange={(date) =>
                  startDateChangeHandler(formatDate(date), end_date)
                }
                clearIcon={null}
                value={start_date}
              />
            </ToolbarItem>
            <ToolbarItem variant="label" className="to-text">
              to
            </ToolbarItem>
            <ToolbarItem>
              <DatePicker
                onChange={(date) =>
                  endDateChangeHandler(start_date, formatDate(date))
                }
                minDate={new Date(start_date)}
                clearIcon={null}
                value={end_date}
              />
            </ToolbarItem>
          </ToolbarContent>
          <ToolbarContent id="comparison-switch">
            <ToolbarItem>
              <Switch
                label="Comparison"
                isChecked={isSwitchChecked}
                onChange={onSwitchChange}
                ouiaId="Comparison Switch"
              />
            </ToolbarItem>
          </ToolbarContent>
        </Toolbar>
      )}
      {Object.keys(appliedFilters).length > 0 && (
        <>
          {Object.entries(appliedFilters).map(([key, values]) => (
            <ChipGroup key={key} numChips={4} categoryName={key}>
              {values.map((i) => (
                <Chip key={i} onClick={() => deleteItem(key, i)}>
                  {i}
                </Chip>
              ))}
            </ChipGroup>
          ))}
          <Button
            variant="link"
            onClick={() => {
              dispatch(removeAllFilters(navigate));
            }}
          >
            Clear all filters
          </Button>
        </>
      )}
    </>
  );
};
ILabFilters.propTypes = {
  filterData: PropTypes.array.isRequired,
  start_date: PropTypes.string,
  end_date: PropTypes.string,
  type: PropTypes.string,
  navigation: PropTypes.func,
  isSwitchChecked: PropTypes.bool,
  onSwitchChange: PropTypes.func,
};
export default ILabFilters;
