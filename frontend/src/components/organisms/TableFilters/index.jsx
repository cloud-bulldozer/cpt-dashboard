import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";
import "./index.less";

import {
  Chip,
  ChipGroup,
  Switch,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";
import {
  removeAppliedFilters,
  setAppliedFilters,
  setCatFilters,
  setDateFilter,
} from "@/actions/filterActions.js";

import ColumnMenuFilter from "@/components/molecules/ColumnMenuFilter";
import DatePicker from "react-date-picker";
import { FilterIcon } from "@patternfly/react-icons";
import MultiSelectBox from "@/components/molecules/MultiSelectBox";
import PropTypes from "prop-types";
import SelectBox from "@/components/molecules/SelectBox";
import { formatDate } from "@/utils/helper";

/**
 * A component that provides an all-in-one toolbar for the tables in this project.
 *
 * Includes a filter selector, a date selector, a column selector, and navigation components.
 * This component utilizes filterActions to modify the data store.
 *
 * @param {*} props:
 *   - tableFilters: A array of name-value pairs mapping the name of the filter category
 *      to the ID of the filter category.
 *   - categoryFilterValue: The ID of the currently selected category. See filterActions.setCatFilters
 *      for relevant code that can influence this input.
 *   - filterOptions: The array of options for the selected category. Used in the multi-select box.
 *      See filterActions.setCatFilters for relevant code that can influence this input.
 *   - appliedFilters: A map/object key-value pairs of the filters that are active.
 *   - start_date: The filter start date
 *   - end_date: The filter end date
 *   - navigation: The react navigate function.
 *   - type: A string that corresponds with the ID used in the commonActions action file.
 *   - showColumnMenu: When true, a toolbar item will display the selectable columns. Requires setColumns.
 *   - setColumns: A callback to set the column with inputs `value`, and `isAdding`. Allows setting
 *      which columns are shown. See ColumnMenuFilter for more information.
 *   - selectedFilters: An array of objects with fields `name` and `value`. `name` is the ID of
 *      the category, and `value` is an array of selected filters within the category.
 *   - updateSelectedFilter: A callback function with inputs `key`, `value`, and `selected` that takes a
 *      key and value for a filter, followed by whether the filter is selected. Used for a multi-select box.
 */
const TableFilter = (props) => {
  const {
    tableFilters,
    categoryFilterValue,
    filterOptions,
    appliedFilters,
    start_date,
    end_date,
    navigation,
    type,
    showColumnMenu,
    setColumns,
    selectedFilters,
    updateSelectedFilter,
    onSwitchChange,
    isSwitchChecked,
    filterData,
    onSwitchChange,
    isSwitchChecked,
  } = props;

  const getFilterCategory = (name) => {
    return tableFilters.filter((item) => item.name === name)?.[0]?.value;
  };

  const getFilterName = (key) => {
    const filter =
      tableFilters?.length > 0 &&
      tableFilters?.find((item) => item.value === key);
    return filter.name;
  };

  const category = getFilterCategory(categoryFilterValue);

  const onCategoryChange = (_event, value) => {
    setCatFilters(value, type);
  };
  const onOptionsChange = async () => {
    const selectedFilterObj = selectedFilters.reduce((acc, item) => {
      if (item.value.length > 0) {
        acc[item.key] = item.value;
      }
      return acc;
    }, {});
    const _ = await import("lodash");
    if (!_.isEqual(selectedFilterObj, appliedFilters)) {
      setAppliedFilters(navigation, type);
    }
  };
  const deleteItem = async (key, value) => {
    await updateSelectedFilter(key, value, false);
    removeAppliedFilters(key, value, navigation, type);
  };
  const startDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  const endDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  return (
    <>
      <Toolbar id="filter-toolbar" ouiaId="data_table_filter">
        {filterData?.length > 0 ? (
          <ToolbarContent className="field-filter">
            <ToolbarItem style={{ marginInlineEnd: 0 }}>
              <SelectBox
                options={filterData}
                onChange={onCategoryChange}
                selected={categoryFilterValue}
                icon={<FilterIcon />}
                width={"200px"}
              />
            </ToolbarItem>
            <ToolbarItem>
              <MultiSelectBox
                options={filterOptions}
                onChange={updateSelectedFilter}
                applyMethod={onOptionsChange}
                currCategory={category}
                selected={selectedFilters?.find((i) => i.name === category)}
                width={"300px"}
              />
            </ToolbarItem>
          </ToolbarContent>
        ) : (
          <ToolbarContent>
            <ToolbarItem variant="label">No filters present</ToolbarItem>
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
                endDateChangeHandler(formatDate(date), start_date)
              }
              minDate={new Date(start_date)}
              clearIcon={null}
              value={end_date}
            />
          </ToolbarItem>
          {showColumnMenu && (
            <ToolbarItem>
              <ColumnMenuFilter type={type} setColumns={setColumns} />
            </ToolbarItem>
          )}
        </ToolbarContent>
        {type === "ilab" && (
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
        )}
      </Toolbar>
      {appliedFilters &&
        Object.keys(appliedFilters).length > 0 &&
        Object.keys(appliedFilters).map((key) => (
          <ChipGroup key={key} numChips={4}>
            {getFilterName(key)} :
            {appliedFilters[key].map((i) => (
              <Chip onClick={() => deleteItem(key, i)} key={i}>
                {i}
              </Chip>
            ))}
          </ChipGroup>
        ))}
    </>
  );
};

TableFilter.propTypes = {
  tableFilters: PropTypes.array.isRequired,
  filterData: PropTypes.array.isRequired,
  categoryFilterValue: PropTypes.string,
  filterOptions: PropTypes.array.isRequired,
  appliedFilters: PropTypes.object,
  start_date: PropTypes.string,
  end_date: PropTypes.string,
  type: PropTypes.string,
  showColumnMenu: PropTypes.bool,
  setColumns: PropTypes.func,
  selectedFilters: PropTypes.array,
  updateSelectedFilter: PropTypes.func.isRequired,
  navigation: PropTypes.func,
  isSwitchChecked: PropTypes.bool,
  onSwitchChange: PropTypes.func,
};
export default TableFilter;
