import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";
import "./index.less";

import {
  Chip,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";

import DatePicker from "react-date-picker";
import { FilterIcon } from "@patternfly/react-icons";
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
    onCategoryChange,
    onOptionsChange,
    deleteItem,
    startDateChangeHandler,
    endDateChangeHandler,
  } = props;

  const category = filterData.filter(
    (item) => item.name === categoryFilterValue
  )[0].key;

  const getFilterName = (key) => {
    const filter = tableFilters.find((item) => item.value === key);
    return filter.name;
  };

  return (
    <>
      <Toolbar id="filter-toolbar">
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
            <SelectBox
              options={filterOptions}
              onChange={onOptionsChange}
              selected={appliedFilters[category] ?? "Select a value"}
              width={"300px"}
            />
          </ToolbarItem>
        </ToolbarContent>
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
        </ToolbarContent>
      </Toolbar>
      {Object.keys(appliedFilters).length > 0 &&
        Object.keys(appliedFilters).map((key) => (
          <Chip key={key} onClick={() => deleteItem(key)}>
            {getFilterName(key)} : {appliedFilters[key]}
          </Chip>
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
  onCategoryChange: PropTypes.func,
  onOptionsChange: PropTypes.func,
  deleteItem: PropTypes.func,
  startDateChangeHandler: PropTypes.func,
  endDateChangeHandler: PropTypes.func,
};
export default TableFilter;
