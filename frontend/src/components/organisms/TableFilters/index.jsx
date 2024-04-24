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
} from "@/actions/homeActions";
import { useDispatch, useSelector } from "react-redux";

import SelectBox from "@/components/molecules/SelectBox";
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
  } = useSelector((state) => state.cpt);
  const category = filterData.filter(
    (item) => item.name === categoryFilterValue
  )[0].key;
  const onCategoryChange = (_event, value) => {
    dispatch(setCatFilters(value));
  };
  const onOptionsChange = (_event, value) => {
    console.log(value);
    dispatch(setAppliedFilters(value, navigate));
  };
  const deleteItem = (key) => {
    console.log("hey");
    dispatch(removeAppliedFilters(key, navigate));
  };
  const getFilterName = (key) => {
    const filter = tableFilters.find((item) => item.value === key);
    return filter.name;
  };
  return (
    <>
      <Toolbar id="filter-toolbar">
        <ToolbarContent>
          <ToolbarItem>
            <SelectBox
              options={tableFilters}
              onChange={onCategoryChange}
              selected={categoryFilterValue}
            />
          </ToolbarItem>
          <ToolbarItem>
            <SelectBox
              options={filterOptions}
              onChange={onOptionsChange}
              selected={appliedFilters[category]}
            />
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>
      {Object.keys(appliedFilters).map((key) => (
        <Chip key={key} onClick={() => deleteItem(key)}>
          {getFilterName(key)} : {appliedFilters[key]}
        </Chip>
      ))}
    </>
  );
};

export default TableFilter;
