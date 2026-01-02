import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";
import {
  INITAL_OFFSET,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import {
  deleteAppliedFilters,
  getRequestParams,
  calculateSummary,
  getSelectedFilter,
} from "./commonActions";
import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import { setLastUpdatedTime } from "./headerActions";

import { cloneDeep } from "lodash";
import { OTHERS } from "@/assets/constants/jobStatusConstants.js";

export const fetchOSOJobs = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });

    const params = dispatch(getRequestParams("oso"));

    const response = await API.get(API_ROUTES.OSO_JOBS_API_V1, { params });

    if (response.status === 200) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_OSO_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }

    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_OSO_JOBS_DATA,
        payload: response.data.results,
      });

      dispatch(tableReCalcValues());
      dispatch({
        type: TYPES.SET_OSO_PAGE_TOTAL,
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
export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().oso.tableColumns];
  const tableFilters = getState().oso.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_OSO_COLUMNS,
    payload: tableColumns,
  });
};

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().oso;

  dispatch(setOSOPageOptions(page, perPage));
};

export const setOSOPage = (pageNo) => ({
  type: TYPES.SET_OSO_PAGE,
  payload: pageNo,
});

export const setOSOPageOptions = (page, perPage) => ({
  type: TYPES.SET_OSO_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const setOSOoffset = (offset) => ({
  type: TYPES.SET_OSO_OFFSET,
  payload: offset,
});

export const setOSOSortIndex = (index) => ({
  type: TYPES.SET_OSO_SORT_INDEX,
  payload: index,
});

export const setOSOSortDir = (direction) => ({
  type: TYPES.SET_OSO_SORT_DIR,
  payload: direction,
});

export const setOSOOtherSummaryFilter = () => (dispatch, getState) => {
  const summary = getState().oso.summary;
  if (summary?.othersCount > 0) {
    dispatch(setSelectedFilter("jobStatus", OTHERS, false));
    dispatch(setOSOAppliedFilters());
  }
};

export const getOSOSummary = (countObj) => (dispatch) => {
  const summary = calculateSummary(countObj);
  dispatch({
    type: TYPES.SET_OSO_SUMMARY,
    payload: summary,
  });
};

export const setOSOCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().oso.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_OSO_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_OSO_FILTER_OPTIONS,
    payload: list,
  });
};

export const setSelectedOSOFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().oso.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_SELECTED_OSO_FILTERS,
    payload: selectedFilters,
  });
};

export const setOSOFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OSO_APPLIED_FILTERS,
  payload: searchParams,
});

export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "oso", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_SELECTED_OSO_FILTERS,
      payload: selectedFilters,
    });
  };
export const setOSOAppliedFilters = (navigate) => (dispatch, getState) => {
  const { start_date, end_date, selectedFilters } = getState().oso;
  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_OSO_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const removeOSOAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "oso")
    );
    const { start_date, end_date } = getState().oso;
    dispatch({
      type: TYPES.SET_OSO_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch) => {
  dispatch(setOSOoffset(INITAL_OFFSET));
  dispatch(setOSOPage(START_PAGE));
  dispatch(fetchOSOJobs());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
};

export const setOSODateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().oso.appliedFilters;

    dispatch({
      type: TYPES.SET_OSO_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  };

export const applyOSODateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setOSOoffset(INITAL_OFFSET));
    dispatch(setOSOPage(START_PAGE));
    dispatch(setOSODateFilter(start_date, end_date, navigate));
    dispatch(fetchOSOJobs());
    dispatch(buildFilterData());
  };

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    const { tableFilters, categoryFilterValue } = getState().oso;

    const params = dispatch(getRequestParams("oso"));

    const response = await API.get(API_ROUTES.OSO_FILTERS_API_V1, { params });
    if (response.status === 200 && response?.data?.filterData?.length > 0) {
      dispatch(getOSOSummary(response.data.summary));
      dispatch({
        type: TYPES.SET_OSO_FILTER_DATA,
        payload: response.data.filterData,
      });
      const activeFilter = categoryFilterValue || tableFilters[0].name;
      dispatch(setOSOCatFilters(activeFilter));
    }
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
  }
};
