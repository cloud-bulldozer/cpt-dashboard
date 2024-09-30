import * as TYPES from "@/actions/types.js";

import { fetchOCPJobs, setOCPCatFilters } from "./ocpActions";

import { cloneDeep } from "lodash";
import { setCPTCatFilters } from "./homeActions";
import { setQuayCatFilters } from "./quayActions";
import { setTelcoCatFilters } from "./telcoActions";

export const sortTable = (colName, currState) => (dispatch, getState) => {
  const { activeSortDir, activeSortIndex } = getState()[currState];
  const countObj = [
    "masterNodesCount",
    "workerNodesCount",
    "infraNodesCount",
    "totalNodesCount",
    "startDate",
    "endDate",
  ];
  try {
    if (activeSortIndex !== null && typeof activeSortIndex !== "undefined") {
      dispatch({ type: TYPES.SET_OCP_OFFSET, payload: 1 });
      const fieldName = countObj.includes(colName)
        ? colName
        : `${colName}.keyword`;
      const sortObj = { [fieldName]: { order: activeSortDir } };
      dispatch({ type: TYPES.SET_OCP_SORT_OBJ, payload: sortObj });
      console.log(sortObj);
      const isFromSorting = true;

      dispatch(fetchOCPJobs(isFromSorting));
    }
  } catch (error) {
    console.log(error);
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
  const categoryFilterValue = getState()[currState].categoryFilterValue;

  const tableFilters = [...getState()[currState].tableFilters];

  const filterData = [];
  for (const filter of tableFilters) {
    const key = filter.value;
    let obj = {
      name: filter.name,
      key,
      value: [
        ...new Set(results.map((item) => item[key]?.toString()?.toLowerCase())),
      ],
    };
    filterData.push(obj);
  }
  dispatch(
    setFilterData(
      filterData,
      currState,
      categoryFilterValue || tableFilters[0].name
    )
  );
};

const setFilterData = (filterData, currState, activeFilter) => (dispatch) => {
  if (currState === "ocp") {
    dispatch({
      type: TYPES.SET_OCP_FILTER_DATA,
      payload: filterData,
    });
    dispatch(setOCPCatFilters(activeFilter));
  } else if (currState === "cpt") {
    dispatch({
      type: TYPES.SET_CPT_FILTER_DATA,
      payload: filterData,
    });
    dispatch(setCPTCatFilters(activeFilter));
  } else if (currState === "quay") {
    dispatch({
      type: TYPES.SET_QUAY_FILTER_DATA,
      payload: filterData,
    });
    dispatch(setQuayCatFilters(activeFilter));
  } else if (currState === "telco") {
    dispatch({
      type: TYPES.SET_TELCO_FILTER_DATA,
      payload: filterData,
    });
    dispatch(setTelcoCatFilters(activeFilter));
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
        const valueMap = appliedFilters[key]?.map((i) =>
          i?.toString()?.toLowerCase()
        );
        if (!valueMap.includes(el[key]?.toString()?.toLowerCase())) {
          return false;
        }
      }
      return true;
    });
  }
  return filtered;
};

export const deleteAppliedFilters =
  (filterKey, filterValue, currState) => (dispatch, getState) => {
    const appliedFilters = cloneDeep(getState()[currState].appliedFilters);

    const index = appliedFilters[filterKey].indexOf(
      filterValue?.toString()?.toLowerCase()
    );
    if (index >= 0) {
      appliedFilters[filterKey].splice(index, 1);
      if (appliedFilters[filterKey].length === 0) {
        delete appliedFilters[filterKey];
      }
    }
    return appliedFilters;
  };

export const getSelectedFilter =
  (selectedCategory, selectedOption, currState, isFromMetrics) =>
  (dispatch, getState) => {
    const selectedFilters = cloneDeep(getState()[currState].selectedFilters);

    const obj = selectedFilters.find((i) => i.name === selectedCategory);
    selectedOption = selectedOption?.toString()?.toLowerCase();

    const objValue = obj.value.map((i) => i?.toString()?.toLowerCase());

    if (objValue.includes(selectedOption)) {
      const arr = objValue.filter((selection) => selection !== selectedOption);
      obj.value = arr;
    } else {
      obj.value = isFromMetrics
        ? [selectedOption]
        : [...obj.value, selectedOption];
    }

    return selectedFilters;
  };
