import { Toolbar, ToolbarContent, ToolbarItem } from "@patternfly/react-core";
import { useDispatch, useSelector } from "react-redux";

import SelectBox from "@/components/molecules/SelectBox";
import { setCatFilters } from "@/actions/homeActions";

const TableFilter = () => {
  const dispatch = useDispatch();
  const { tableFilters, categoryFilterValue, filterOptions } = useSelector(
    (state) => state.cpt
  );

  const onCategoryChange = (_event, value) => {
    dispatch(setCatFilters(value));
  };
  const onOptionsChange = (_event, value) => {
    console.log(value);
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
              selected=""
            />
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>
    </>
  );
};

export default TableFilter;
