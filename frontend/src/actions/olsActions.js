import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import {
  deleteAppliedFilters,
  getRequestParams,
  getSelectedFilter,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { INITAL_OFFSET } from "@/assets/constants/paginationConstants";
import { cloneDeep } from "lodash";
import { setLastUpdatedTime } from "./headerActions";
import { showFailureToast } from "./toastActions";

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
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_OLS_JOBS_DATA,
        payload: response.data.results,
      });

      dispatch({
        type: TYPES.SET_OLS_PAGE_TOTAL,
        payload: {
          total: response.data.total,
          offset: response.data.offset,
        },
      });
      dispatch(tableReCalcValues());
    }
    dispatch(setLastUpdatedTime());
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

export const applyFilters = () => (dispatch) => {
  dispatch(setOLSOffset(INITAL_OFFSET));
  dispatch(fetchOLSJobsData());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
};

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().ols.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_SELECTED_OLS_FILTERS,
    payload: selectedFilters,
  });
};
export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "ols", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_SELECTED_OLS_FILTERS,
      payload: selectedFilters,
    });
  };
export const setOLSAppliedFilters = (navigate) => (dispatch, getState) => {
  const { start_date, end_date, selectedFilters } = getState().ols;
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

export const removeOLSAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "ols")
    );
    const { start_date, end_date } = getState().ols;
    dispatch({
      type: TYPES.SET_OLS_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
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
    dispatch(setOLSDateFilter(start_date, end_date, navigate));
    dispatch(fetchOLSJobsData());
    dispatch(buildFilterData());
  };
export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OLS_APPLIED_FILTERS,
  payload: searchParams,
});

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

export const getOLSSummary = (countObj) => (dispatch) => {
  const other =
    countObj["total"] -
    ((countObj["success"] || 0) + (countObj["failure"] || 0));
  const summary = {
    othersCount: other,
    successCount: countObj["success"] || 0,
    failureCount: countObj["failure"] || 0,
    total: countObj["total"],
  };
  dispatch({
    type: TYPES.SET_OLS_SUMMARY,
    payload: summary,
  });
};

export const fetchGraphData =
  (uuid, nodeName) => async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.GRAPH_LOADING });

      const graphData = getState().ols.graphData;
      const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
      if (!hasData) {
        const response = await API.get(
          `${API_ROUTES.OLS_GRAPH_API_V1}/${uuid}`
        );

        if (response.status === 200) {
          dispatch({
            type: TYPES.SET_OLS_GRAPH_DATA,
            payload: { uuid, data: [[nodeName, response.data]] },
          });
        }
      }
    } catch (error) {
      dispatch(showFailureToast());
    }
    dispatch({ type: TYPES.GRAPH_COMPLETED });
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
    dispatch(showFailureToast());
  }
};
