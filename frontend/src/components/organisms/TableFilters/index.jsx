import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";
import "./index.less";

import {
  Banner,
  Chip,
  ChipGroup,
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
  } = props;

  const getFilterID = (name) => {
    if (!(tableFilters?.length > 0)) {
      return "";
    }
    const filterResults = tableFilters.filter((item) => item.name === name);
    if (filterResults.length == 0) {
      return "";
    }
    return filterResults[0].value
  }

  const getFilterName = (key) => {
    const filter =
      tableFilters?.length > 0 &&
      tableFilters?.find((item) => item.value === key);
    return filter.name;
  };

  const category = getFilterID(categoryFilterValue);

  const onCategoryChange = (_event, value) => {
    setCatFilters(value, type);
  };
  const onOptionsChange = () => {
    setAppliedFilters(navigation, type);
  };
  const deleteItem = (key, value) => {
    updateSelectedFilter(key, value, false);
    removeAppliedFilters(key, value, navigation, type);
  };
  const startDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  const endDateChangeHandler = (date, key) => {
    setDateFilter(key, date, navigation, type);
  };
  return (
    <>
      <Toolbar id="filter-toolbar">
        {tableFilters != null && filterOptions != null && updateSelectedFilter != null && (
          tableFilters.length > 0 ? (
            <ToolbarContent className="field-filter">
              <ToolbarItem style={{ marginInlineEnd: 0 }}>
                <SelectBox
                  options={tableFilters}
                  onChange={onCategoryChange}
                  selected={categoryFilterValue}
                  icon={<FilterIcon />}
                  width={"200px"}
                />
              </ToolbarItem>
              <ToolbarItem>
                {filterOptions.length > 0 ? (
                  <MultiSelectBox
                    options={filterOptions}
                    onChange={updateSelectedFilter}
                    applyMethod={onOptionsChange}
                    currCategory={category}
                    selected={selectedFilters?.find((i) => i.name === category)}
                    width={"300px"}
                  />
                ) :
                  <Banner status="warning">No options for category "{category}"</Banner>
                }
              </ToolbarItem>
            </ToolbarContent>
          ) :
            <ToolbarContent>
              <ToolbarItem variant="label">No filters present</ToolbarItem>
            </ToolbarContent>
        )}

        <ToolbarContent className="date-filter">
          <ToolbarItem>
            <DatePicker
              onChange={(date) =>
                startDateChangeHandler(formatDate(date), end_date)
              }
              clearIcon={null}
              value={start_date}
            />
          </ToolbarItem>
          <ToolbarItem className="to-text">to</ToolbarItem>
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
      </Toolbar>
      {Object.keys(appliedFilters).length > 0 &&
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
  tableFilters: PropTypes.array,
  categoryFilterValue: PropTypes.string,
  filterOptions: PropTypes.array,
  appliedFilters: PropTypes.object,
  start_date: PropTypes.string,
  end_date: PropTypes.string,
  type: PropTypes.string,
  showColumnMenu: PropTypes.bool,
  setColumns: PropTypes.func,
  selectedFilters: PropTypes.array,
  updateSelectedFilter: PropTypes.func,
  navigation: PropTypes.func,
};
export default TableFilter;
