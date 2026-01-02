import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  INITAL_OFFSET,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import {
  calculateSummary,
  deleteAppliedFilters,
  getRequestParams,
  getSelectedFilter,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { setLastUpdatedTime } from "./headerActions";
import { OTHERS } from "@/assets/constants/jobStatusConstants";

export const fetchOLSJobsData = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });

    const params = dispatch(getRequestParams("ols"));
    const response = await API.get(API_ROUTES.OLS_JOBS_API_V1, { params });
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
    const hasResults = response.data?.results?.length > 0;
    dispatch({
      type: TYPES.SET_OLS_JOBS_DATA,
      payload: hasResults ? response.data.results : [],
    });
    dispatch({
      type: TYPES.SET_OLS_FILTERED_DATA,
      payload: hasResults ? response.data.results : [],
    });

    if (hasResults) {
      dispatch(tableReCalcValues());
      dispatch({
        type: TYPES.SET_OLS_PAGE_TOTAL,
        payload: {
          total: response.data.total,
          offset: response.data.offset,
        },
      });
    }

    dispatch(setLastUpdatedTime());
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
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

export const setOLSOffset = (offset) => ({
  type: TYPES.SET_OLS_OFFSET,
  payload: offset,
});

export const setOLSSortIndex = (index) => ({
  type: TYPES.SET_OLS_SORT_INDEX,
  payload: index,
});

export const setOLSSortDir = (direction) => ({
  type: TYPES.SET_OLS_SORT_DIR,
  payload: direction,
});

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

export const applyFilters = () => (dispatch) => {
  dispatch(setOLSOffset(INITAL_OFFSET));
  dispatch(setOLSPage(START_PAGE));
  dispatch(fetchOLSJobsData());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
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

export const setSelectedOLSFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().ols.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_OLS_SELECTED_FILTERS,
    payload: selectedFilters,
  });
};

export const setOLSFilterFromURL = (searchParams) => ({
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
  };

export const applyOLSDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setOLSOffset(INITAL_OFFSET));
    dispatch(setOLSPage(START_PAGE));
    dispatch(setOLSDateFilter(start_date, end_date, navigate));
    dispatch(fetchOLSJobsData());
    dispatch(buildFilterData());
  };

export const setOLSOtherSummaryFilter = () => (dispatch, getState) => {
  const summary = getState().ols.summary;
  if (summary?.othersCount !== 0) {
    dispatch(setSelectedFilter("jobStatus", OTHERS, false));
    dispatch(setOLSAppliedFilters());
  }
};

export const getOLSSummary = (countObj) => (dispatch) => {
  const summary = calculateSummary(countObj);
  dispatch({
    type: TYPES.SET_OLS_SUMMARY,
    payload: summary,
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

export const fetchGraphData = (uuid) => async (dispatch, getState) => {
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
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
  }
  dispatch({ type: TYPES.GRAPH_COMPLETED });
};

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ols;

  dispatch(setOLSPageOptions(page, perPage));
};

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    const { tableFilters, categoryFilterValue } = getState().ols;

    const params = dispatch(getRequestParams("ols"));

    const response = await API.get(API_ROUTES.OLS_FILTERS_API_V1, { params });
    if (response.status === 200 && response?.data?.filterData?.length > 0) {
      dispatch(getOLSSummary(response.data.summary));
      dispatch({
        type: TYPES.SET_OLS_FILTER_DATA,
        payload: response.data.filterData,
      });
      const activeFilter = categoryFilterValue || tableFilters[0].name;
      dispatch(setOLSCatFilters(activeFilter));
    }
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
  }
};
