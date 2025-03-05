import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import {
  buildFilterData,
  calculateMetrics,
  deleteAppliedFilters,
  getFilteredData,
  getSelectedFilter,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { showFailureToast } from "@/actions/toastActions";

export const fetchOLSJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().ols;
    const response = await API.get(API_ROUTES.OLS_JOBS_API_V1, {
      params: {
        pretty: true,
        ...(start_date && { start_date }),
        ...(end_date && { end_date }),
      },
    });
    if (response.status === 200) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_OLS_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_OLS_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_OLS_FILTERED_DATA,
        payload: response.data.results,
      });
      dispatch(applyFilters());
      dispatch(tableReCalcValues());
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const setOLSPage = (pageNo) => ({
  type: TYPES.SET_OLS_PAGE,
  payload: pageNo,
});

export const setOLSPageOptions = (page, perPage) => ({
  type: TYPES.SET_OLS_PAGE_OPTIONS,
  payload: { page, perPage },
});
export const setOLSSortIndex = (index) => ({
  type: TYPES.SET_OLS_SORT_INDEX,
  payload: index,
});

export const setOLSSortDir = (direction) => ({
  type: TYPES.SET_OLS_SORT_DIR,
  payload: direction,
});
export const sliceOLSTableRows =
  (startIdx, endIdx) => (dispatch, getState) => {
    const results = [...getState().ols.filteredResults];

    dispatch({
      type: TYPES.SET_OLS_INIT_JOBS,
      payload: results.slice(startIdx, endIdx),
    });
  };

export const setOLSCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().ols.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_OLS_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_OLS_FILTER_OPTIONS,
    payload: list,
  });
};
export const removeOLSAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const { start_date, end_date } = getState().ols;

    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "ols")
    );

    dispatch({
      type: TYPES.SET_OLS_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().ols;

  const results = [...getState().ols.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    Object.values(appliedFilters).flat().length > 0;

  const filtered = isFilterApplied
    ? getFilteredData(appliedFilters, results)
    : results;

  dispatch({
    type: TYPES.SET_OLS_FILTERED_DATA,
    payload: filtered,
  });
  dispatch(tableReCalcValues());
  dispatch(buildFilterData("ols"));
};
export const setOLSAppliedFilters = (navigate) => (dispatch, getState) => {
  const { selectedFilters, start_date, end_date } = getState().ols;

  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_OLS_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().ols.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_OLS_SELECTED_FILTERS,
    payload: selectedFilters,
  });
};

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OLS_APPLIED_FILTERS,
  payload: searchParams,
});

export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "ols", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_OLS_SELECTED_FILTERS,
      payload: selectedFilters,
    });
  };
export const setOLSDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().ols.appliedFilters;

    dispatch({
      type: TYPES.SET_OLS_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);

    dispatch(fetchOLSJobsData());
  };

export const setOLSOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().ols.filteredResults];
  const keyWordArr = ["success", "failure"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  dispatch({
    type: TYPES.SET_OLS_FILTERED_DATA,
    payload: data,
  });
  dispatch(tableReCalcValues());
};

export const getOLSSummary = () => (dispatch, getState) => {
  const results = [...getState().ols.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_OLS_SUMMARY,
    payload: countObj,
  });
};

export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().ols.tableColumns];
  const tableFilters = getState().ols.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_OLS_COLUMNS,
    payload: tableColumns,
  });
};

export const fetchOLSGraphData = (uuid) => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.GRAPH_LOADING });

    const graphData = getState().ocp.graphData;
    const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
    if (!hasData) {
      const response = await API.get(`${API_ROUTES.OLS_GRAPH_API_V1}/${uuid}`);

      if (response.status === 200) {
        const result = Object.keys(response.data).map((key) => [
          key,
          response.data[key],
        ]);
        dispatch({
          type: TYPES.SET_OLS_GRAPH_DATA,
          payload: { uuid, data: result },
        });
      }
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.GRAPH_COMPLETED });
};

export const tableReCalcValues = () => (dispatch) => {
  dispatch(getOLSSummary());
  dispatch(setOLSPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceOLSTableRows(0, DEFAULT_PER_PAGE));
};
