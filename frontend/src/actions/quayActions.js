import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import {
  buildFilterData,
  calculateMetrics,
  deleteAppliedFilters,
  getFilteredData,
  getRequestParams,
  getSelectedFilter,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { showFailureToast } from "@/actions/toastActions";

export const fetchQuayJobsData = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });

    const params = dispatch(getRequestParams("quay"));
    const response = await API.get(API_ROUTES.QUAY_JOBS_API_V1, { params });
    if (response.status === 200) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_QUAY_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_QUAY_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_QUAY_FILTERED_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_QUAY_PAGE_TOTAL,
        payload: {
          total: response.data.total,
          offset: response.data.offset,
        },
      });
      dispatch(applyFilters());
      dispatch(tableReCalcValues());
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const setQuayPage = (pageNo) => ({
  type: TYPES.SET_QUAY_PAGE,
  payload: pageNo,
});

export const setQuayPageOptions = (page, perPage) => ({
  type: TYPES.SET_QUAY_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const setQuayOffset = (offset) => ({
  type: TYPES.SET_QUAY_OFFSET,
  payload: offset,
});

export const setQuaySortIndex = (index) => ({
  type: TYPES.SET_QUAY_SORT_INDEX,
  payload: index,
});

export const setQuaySortDir = (direction) => ({
  type: TYPES.SET_QUAY_SORT_DIR,
  payload: direction,
});

export const setQuayCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().quay.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_QUAY_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_QUAY_FILTER_OPTIONS,
    payload: list,
  });
};
export const removeQuayAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const { start_date, end_date } = getState().quay;

    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "quay")
    );

    dispatch({
      type: TYPES.SET_QUAY_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().quay;

  const results = [...getState().quay.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    Object.values(appliedFilters).flat().length > 0;

  const filtered = isFilterApplied
    ? getFilteredData(appliedFilters, results)
    : results;

  dispatch({
    type: TYPES.SET_QUAY_FILTERED_DATA,
    payload: filtered,
  });
  dispatch(tableReCalcValues());
  dispatch(buildFilterData("quay"));
};
export const setQuayAppliedFilters = (navigate) => (dispatch, getState) => {
  const { selectedFilters, start_date, end_date } = getState().quay;

  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_QUAY_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().quay.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_QUAY_SELECTED_FILTERS,
    payload: selectedFilters,
  });
};

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_QUAY_APPLIED_FILTERS,
  payload: searchParams,
});

export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "quay", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_QUAY_SELECTED_FILTERS,
      payload: selectedFilters,
    });
  };
export const setQuayDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().quay.appliedFilters;

    dispatch({
      type: TYPES.SET_QUAY_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);

    dispatch(fetchQuayJobsData());
  };

export const setQuayOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().quay.filteredResults];
  const keyWordArr = ["success", "failure"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  dispatch({
    type: TYPES.SET_QUAY_FILTERED_DATA,
    payload: data,
  });
  dispatch(tableReCalcValues());
};

export const getQuaySummary = () => (dispatch, getState) => {
  const results = [...getState().quay.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_QUAY_SUMMARY,
    payload: countObj,
  });
};

export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().quay.tableColumns];
  const tableFilters = getState().quay.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_QUAY_COLUMNS,
    payload: tableColumns,
  });
};

export const fetchGraphData = (uuid) => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.GRAPH_LOADING });

    const graphData = getState().ocp.graphData;
    const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
    if (!hasData) {
      const response = await API.get(`${API_ROUTES.QUAY_GRAPH_API_V1}/${uuid}`);

      if (response.status === 200) {
        const result = Object.keys(response.data).map((key) => [
          key,
          response.data[key],
        ]);
        dispatch({
          type: TYPES.SET_QUAY_GRAPH_DATA,
          payload: { uuid, data: result },
        });
      }
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.GRAPH_COMPLETED });
};

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().quay;
  dispatch(getQuaySummary());
  dispatch(setQuayPageOptions(page, perPage));
};
