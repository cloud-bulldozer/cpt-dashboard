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

export const fetchTelcoJobsData = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });

    const params = dispatch(getRequestParams("telco"));

    const response = await API.get(API_ROUTES.TELCO_JOBS_API_V1, { params });
    if (response.status === 200) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_TELCO_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }
    const hasResults = response.data?.results?.length > 0;
    dispatch({
      type: TYPES.SET_TELCO_JOBS_DATA,
      payload: hasResults ? response.data.results : [],
    });
    dispatch({
      type: TYPES.SET_TELCO_FILTERED_DATA,
      payload: hasResults ? response.data.results : [],
    });
    if (hasResults) {
      dispatch(tableReCalcValues());
      dispatch({
        type: TYPES.SET_TELCO_PAGE_TOTAL,
        payload: {
          total: Number(response.data.total),
          offset: response.data.offset,
        },
      });
    }
    dispatch(setLastUpdatedTime());
  } catch (error) {
    console.error(error);
  }
  dispatch({ type: TYPES.COMPLETED });
};
export const setTelcoPage = (pageNo) => ({
  type: TYPES.SET_TELCO_PAGE,
  payload: pageNo,
});

export const setTelcoPageOptions = (page, perPage) => ({
  type: TYPES.SET_TELCO_PAGE_OPTIONS,
  payload: { page, perPage },
});
export const setTelcoSortIndex = (index) => ({
  type: TYPES.SET_TELCO_SORT_INDEX,
  payload: index,
});
export const setTelcoOffset = (offset) => ({
  type: TYPES.SET_TELCO_OFFSET,
  payload: offset,
});
export const setTelcoSortDir = (direction) => ({
  type: TYPES.SET_TELCO_SORT_DIR,
  payload: direction,
});

export const setTelcoCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().telco.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_TELCO_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_TELCO_FILTER_OPTIONS,
    payload: list,
  });
};
export const removeTelcoAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const { start_date, end_date } = getState().telco;

    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "telco")
    );

    dispatch({
      type: TYPES.SET_TELCO_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };
export const applyFilters = () => (dispatch) => {
  dispatch(setTelcoOffset(INITAL_OFFSET));
  dispatch(setTelcoPage(START_PAGE));
  dispatch(fetchTelcoJobsData());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
};
export const setTelcoAppliedFilters = (navigate) => (dispatch, getState) => {
  const { selectedFilters, start_date, end_date } = getState().telco;

  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_TELCO_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const setTelcoFilterFromURL = (searchParams) => ({
  type: TYPES.SET_TELCO_APPLIED_FILTERS,
  payload: searchParams,
});

export const setSelectedTelcoFilterFromUrl =
  (params) => (dispatch, getState) => {
    const selectedFilters = cloneDeep(getState().telco.selectedFilters);
    for (const key in params) {
      selectedFilters.find((i) => i.name === key).value =
        params[key].split(",");
    }
    dispatch({
      type: TYPES.SET_TELCO_SELECTED_FILTERS,
      payload: selectedFilters,
    });
  };

export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(
        selectedCategory,
        selectedOption,
        "telco",
        isFromMetrics
      )
    );
    dispatch({
      type: TYPES.SET_TELCO_SELECTED_FILTERS,
      payload: selectedFilters,
    });
  };

export const setTelcoDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().telco.appliedFilters;

    dispatch({
      type: TYPES.SET_TELCO_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  };

export const applyTelcoDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setTelcoOffset(INITAL_OFFSET));
    dispatch(setTelcoPage(START_PAGE));
    dispatch(setTelcoDateFilter(start_date, end_date, navigate));
    dispatch(fetchTelcoJobsData());
    dispatch(buildFilterData());
  };

export const getTelcoSummary = (countObj) => (dispatch) => {
  const summary = calculateSummary(countObj);
  dispatch({
    type: TYPES.SET_TELCO_SUMMARY,
    payload: summary,
  });
};

export const setTelcoOtherSummaryFilter = () => (dispatch, getState) => {
  const summary = getState().telco.summary;
  if (summary?.othersCount !== 0) {
    dispatch(setSelectedFilter("jobStatus", OTHERS, false));
    dispatch(setTelcoAppliedFilters());
  }
};
export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().telco.tableColumns];
  const tableFilters = getState().telco.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_TELCO_COLUMNS,
    payload: tableColumns,
  });
};
export const fetchGraphData =
  (benchmark, uuid, encryption) => async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.GRAPH_LOADING });

      const graphData = getState().ocp.graphData;
      const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
      if (!hasData) {
        const response = await API.get(
          `${API_ROUTES.TELCO_GRAPH_API_V1}/${uuid}/${encryption}`
        );

        if (response.status === 200) {
          let result;
          if (
            ["oslat", "cyclictest", "deployment", "cpu_util"].includes(
              benchmark
            )
          ) {
            const benchmarkData = response.data[benchmark];
            result = Object.keys(response.data[benchmark]).map((key) => [
              key,
              benchmarkData[key],
            ]);
          } else {
            result = Object.keys(response.data).map((key) => [
              key,
              response.data[key],
            ]);
          }

          dispatch({
            type: TYPES.SET_TELCO_GRAPH_DATA,
            payload: { uuid, data: result },
          });
        }
      }
    } catch (error) {
      console.error(error);
    }
    dispatch({ type: TYPES.GRAPH_COMPLETED });
  };
export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().telco;
  dispatch(setTelcoPageOptions(page, perPage));
};

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    const { tableFilters, categoryFilterValue } = getState().telco;

    const params = dispatch(getRequestParams("telco"));

    const response = await API.get("/api/v1/telco/filters", { params });

    if (response.status === 200 && response?.data?.filterData?.length > 0) {
      dispatch(getTelcoSummary(response.data.summary));
      dispatch({
        type: TYPES.SET_TELCO_FILTER_DATA,
        payload: response.data.filterData,
      });
      const activeFilter = categoryFilterValue || tableFilters[0].name;
      dispatch(setTelcoCatFilters(activeFilter));
    }
  } catch (error) {
    console.error(error);
  }
};
