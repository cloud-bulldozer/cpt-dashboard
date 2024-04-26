import "react-date-picker/dist/DatePicker.css";
import "react-calendar/dist/Calendar.css";
import "./index.less";

import {
  Chip,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from "@patternfly/react-core";
import {
  removeAppliedFilters,
  setAppliedFilters,
  setCatFilters,
  setDateFilter,
} from "@/actions/homeActions";
import { useDispatch, useSelector } from "react-redux";

import DatePicker from "react-date-picker";
import { FilterIcon } from "@patternfly/react-icons";
import SelectBox from "@/components/molecules/SelectBox";
import { formatDate } from "@/utils/helper";
import { useNavigate } from "react-router-dom";

const TableFilter = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const {
    tableFilters,
    categoryFilterValue,
    filterOptions,
    filterData,
    appliedFilters,
    start_date,
    end_date,
  } = useSelector((state) => state.cpt);

  const category = filterData.filter(
    (item) => item.name === categoryFilterValue
  )[0].key;
  const onCategoryChange = (_event, value) => {
    dispatch(setCatFilters(value));
  };
  const onOptionsChange = (_event, value) => {
    dispatch(setAppliedFilters(value, navigate));
  };
  const deleteItem = (key) => {
    dispatch(removeAppliedFilters(key, navigate));
  };
  const getFilterName = (key) => {
    const filter = tableFilters.find((item) => item.value === key);
    return filter.name;
  };

  const startDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(date, key, navigate));
  };
  const endDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(key, date, navigate));
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
          <ToolbarItem>to</ToolbarItem>
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

export default TableFilter;
