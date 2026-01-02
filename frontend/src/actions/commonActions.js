import { cloneDeep } from "lodash";

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
    const filterArray = appliedFilters[filterKey];

    if (Array.isArray(filterArray)) {
      const index = filterArray.findIndex(
        (item) =>
          item?.toString()?.toLowerCase() ===
          filterValue?.toString()?.toLowerCase()
      );

      if (index >= 0) {
        filterArray.splice(index, 1);
        if (filterArray.length === 0) {
          delete appliedFilters[filterKey];
        }
      }
    }
    return appliedFilters;
  };

export const getSelectedFilter =
  (selectedCategory, selectedOption, currState, isFromMetrics) =>
  (dispatch, getState) => {
    const selectedFilters = cloneDeep(getState()[currState].selectedFilters);

    const obj = selectedFilters.find((i) => i.name === selectedCategory);

    const objValue = obj.value;
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

const convertObjectToQS = (filter) => {
  const queryString = Object.entries(filter)
    .map(([key, values]) => `${key}='${values.join("','")}'`)
    .join("&");

  return queryString;
};
export const getRequestParams = (type) => (dispatch, getState) => {
  const { start_date, end_date, perPage, offset, sort, appliedFilters } =
    getState()[type];

  let filter = "";
  if (Object.keys(appliedFilters).length > 0) {
    filter = convertObjectToQS(appliedFilters);
  }
  const params = {
    pretty: true,
    ...(start_date && { start_date }),
    ...(end_date && { end_date }),
    size: perPage,
    offset: offset,
    ...(sort && { sort }),
    ...(filter && { filter }),
  };

  return params;
};

export const calculateSummary = (countObj) => {
  const total = Number(countObj?.["total"]) || 0;
  const success = Number(countObj?.["success"]) || 0;
  const failure = Number(countObj?.["failure"]) || 0;
  const others = total - (success + failure);

  const summary = {
    total,
    successCount: success,
    failureCount: failure,
    othersCount: others > 0 ? others : 0,
  };
  return summary;
};
