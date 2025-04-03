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

const TableFilter = (props) => {
  const {
    tableFilters,
    categoryFilterValue,
    filterOptions,
    filterData,
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
  } = props;

  const category =
    filterData?.length > 0 &&
    filterData.filter((item) => item.name === categoryFilterValue)[0].key;

  const getFilterName = (key) => {
    const filter =
      tableFilters?.length > 0 &&
      tableFilters?.find((item) => item.value === key);
    return filter.name;
  };

  const onCategoryChange = (_event, value) => {
    setCatFilters(value, type);
  };
  const onOptionsChange = () => {
    setAppliedFilters(navigation, type);
  };
  const deleteItem = (key, value) => {
    removeAppliedFilters(key, value, navigation, type);
    updateSelectedFilter(key, value, false);
  };
  const startDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };
  const endDateChangeHandler = (date, key) => {
    setDateFilter(date, key, navigation, type);
  };

  return (
    <>
      <Toolbar id="filter-toolbar">
        {tableFilters?.length > 0 && filterOptions?.length > 0 && (
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
  tableFilters: PropTypes.array,
  categoryFilterValue: PropTypes.string,
  filterOptions: PropTypes.array,
  filterData: PropTypes.array,
  appliedFilters: PropTypes.object,
  start_date: PropTypes.string,
  end_date: PropTypes.string,
  type: PropTypes.string,
  showColumnMenu: PropTypes.bool,
  setColumns: PropTypes.func,
  selectedFilters: PropTypes.array,
  updateSelectedFilter: PropTypes.func,
  navigation: PropTypes.func,
  isSwitchChecked: PropTypes.bool,
  onSwitchChange: PropTypes.func,
};
export default TableFilter;
