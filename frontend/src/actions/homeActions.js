import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import API from "@/utils/axiosInstance";
import { DEFAULT_PER_PAGE } from "@/assets/constants/paginationConstants";
import { appendQueryString } from "@/utils/helper";
import { showFailureToast } from "@/actions/toastActions";

export const fetchOCPJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
    const response = await API.get(API_ROUTES.CPT_JOBS_API_V1, {
      params: {
        pretty: true,
        // ...(start_date && { start_date }),
        // ...(end_date && { end_date }),
        start_date: "2024-04-21",
        end_date: "2024-04-22",
      },
    });
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_CPT_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_CPT_DATE_FILTER,
        payload: {
          start_date: response.data.startDate,
          end_date: response.data.endDate,
        },
      });
      dispatch(applyFilters());
      dispatch(sortTable());
      dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
      dispatch(buildFilterData());
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

const getSortableRowValues = (result, tableColumns) => {
  const tableKeys = tableColumns.map((item) => item.value);
  return tableKeys.map((key) => result[key]);
};

export const sortTable = () => (dispatch, getState) => {
  const { activeSortDir, activeSortIndex, tableColumns } = getState().cpt;
  const results = [...getState().cpt.filteredResults];
  try {
    if (activeSortIndex) {
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
      dispatch({
        type: TYPES.SET_CPT_JOBS_DATA,
        payload: sortedResults,
      });
      dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
    }
  } catch (error) {
    console.log(error);
    dispatch(showFailureToast());
  }
};

export const setCPTSortIndex = (index) => ({
  type: TYPES.SET_CPT_SORT_INDEX,
  payload: index,
});

export const setCPTSortDir = (direction) => ({
  type: TYPES.SET_CPT_SORT_DIR,
  payload: direction,
});

export const sliceTableRows = (startIdx, endIdx) => (dispatch, getState) => {
  const results = [...getState().cpt.filteredResults];

  dispatch({
    type: TYPES.SET_CPT_INIT_JOBS,
    payload: results.slice(startIdx, endIdx),
  });
};

export const buildFilterData = () => (dispatch, getState) => {
  const results = [...getState().cpt.results];

  const tableFilters = [...getState().cpt.tableFilters];

  const filterData = [];
  for (const filter of tableFilters) {
    const key = filter.value;
    let obj = {
      name: filter.name,
      key,
      value: [...new Set(results.map((item) => item[key])), "ALL"],
    };
    filterData.push(obj);
  }
  dispatch({
    type: TYPES.SET_CPT_FILTER_DATA,
    payload: filterData,
  });
  dispatch(setCatFilters(tableFilters[0].name));
};

export const setCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().cpt.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_FILTER_OPTIONS,
    payload: list,
  });
};

export const setAppliedFilters =
  (selectedOption, navigate) => (dispatch, getState) => {
    const { categoryFilterValue, filterData } = getState().cpt;
    const appliedFilters = { ...getState().cpt.appliedFilters };

    const category = filterData.filter(
      (item) => item.name === categoryFilterValue
    )[0].key;
    appliedFilters[category] = selectedOption;

    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString(appliedFilters, navigate);
    dispatch(applyFilters());
  };

export const removeAppliedFilters =
  (filterKey, navigate) => (dispatch, getState) => {
    const appliedFilters = { ...getState().cpt.appliedFilters };
    delete appliedFilters[filterKey];
    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString(appliedFilters, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().cpt;

  const results = [...getState().cpt.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    !Object.values(appliedFilters).includes("");

  let filtered = [];
  if (isFilterApplied) {
    filtered = results.filter((el) => {
      for (const key in appliedFilters) {
        if (el[key] !== appliedFilters[key]) {
          return false;
        }
      }
      return true;
    });
  }

  dispatch({
    type: TYPES.SET_FILTERED_DATA,
    payload: isFilterApplied ? filtered : results,
  });
  dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
};

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_APPLIED_FILTERS,
  payload: Object.fromEntries(searchParams),
});

export const setDateFilter = (start_date, end_date) => (dispatch) => {
  dispatch({
    type: TYPES.SET_CPT_DATE_FILTER,
    payload: {
      start_date,
      end_date,
    },
  });
  dispatch(fetchOCPJobsData());
};
