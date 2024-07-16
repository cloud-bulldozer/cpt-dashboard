import * as TYPES from "@/actions/types.js";

import { setOCPCatFilters, sliceOCPTableRows } from "./ocpActions";

import { DEFAULT_PER_PAGE } from "@/assets/constants/paginationConstants";
import { sliceTableRows } from "./homeActions";

const getSortableRowValues = (result, tableColumns) => {
  const tableKeys = tableColumns.map((item) => item.value);
  return tableKeys.map((key) => result[key]);
};

export const sortTable = (currState) => (dispatch, getState) => {
  const results = [...getState()[currState].filteredResults];
  const { activeSortDir, activeSortIndex, tableColumns } =
    getState()[currState];
  try {
    if (activeSortIndex !== null && typeof activeSortIndex !== "undefined") {
      const sortedResults = results.sort((a, b) => {
        const aValue = getSortableRowValues(a, tableColumns)[activeSortIndex];
        const bValue = getSortableRowValues(b, tableColumns)[activeSortIndex];
        if (typeof aValue === "number") {
          if (activeSortDir === "asc") {
            return aValue - bValue;
          }
          return bValue - aValue;
        } else {
          if (activeSortDir === "asc") {
            return aValue.localeCompare(bValue);
          }
          return bValue.localeCompare(aValue);
        }
      });
      dispatch(sortedTableRows(currState, sortedResults));
    }
  } catch (error) {
    console.log(error);
  }
};

const sortedTableRows = (currState, sortedResults) => (dispatch) => {
  if (currState === "cpt") {
    dispatch({
      type: TYPES.SET_FILTERED_DATA,
      payload: sortedResults,
    });
    dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
    return;
  }
  if (currState === "ocp") {
    dispatch({
      type: TYPES.SET_OCP_FILTERED_DATA,
      payload: sortedResults,
    });
    dispatch(sliceOCPTableRows(0, DEFAULT_PER_PAGE));
  }
};

const findItemCount = (data, key, value) => {
  return data.reduce(function (n, item) {
    return n + (item[key].toLowerCase() === value);
  }, 0);
};

export const calculateMetrics = (results) => {
  const keyWordArr = ["success", "failure"];
  const othersCount = results.reduce(function (n, item) {
    return n + !keyWordArr.includes(item.jobStatus?.toLowerCase());
  }, 0);

  const successCount = findItemCount(results, "jobStatus", "success");
  const failureCount = findItemCount(results, "jobStatus", "failure");

  return { successCount, failureCount, othersCount };
};

export const buildFilterData = (currState) => (dispatch, getState) => {
  const results = [...getState()[currState].results];

  const tableFilters = [...getState()[currState].tableFilters];

  const filterData = [];
  for (const filter of tableFilters) {
    const key = filter.value;
    let obj = {
      name: filter.name,
      key,
      value: [...new Set(results.map((item) => item[key]))],
    };
    filterData.push(obj);
  }
  dispatch(setFilterData(filterData, currState, tableFilters[0].name));
};

const setFilterData = (filterData, currState, activeFilter) => (dispatch) => {
  if (currState === "ocp") {
    dispatch({
      type: TYPES.SET_OCP_FILTER_DATA,
      payload: filterData,
    });
    dispatch(setOCPCatFilters(activeFilter));
  }
};

export const getFilteredData = (appliedFilters, results) => {
  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    !Object.values(appliedFilters).includes("");

  let filtered = [];
  if (isFilterApplied) {
    filtered = results.filter((el) => {
      for (const key in appliedFilters) {
        if (
          el[key]?.toString()?.toLowerCase() !==
          appliedFilters[key]?.toString()?.toLowerCase()
        ) {
          return false;
        }
      }
      return true;
    });
  }
  return filtered;
};

export const getAppliedFilters =
  (currState, selectedOption) => (dispatch, getState) => {
    const { categoryFilterValue, filterData } = getState()[currState];
    const appliedFilters = { ...getState()[currState].appliedFilters };

    const category = filterData.filter(
      (item) => item.name === categoryFilterValue
    )[0].key;
    appliedFilters[category] = selectedOption;

    return appliedFilters;
  };
