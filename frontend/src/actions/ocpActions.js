import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

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
import { OTHERS } from "@/assets/constants/jobStatusConstants.js";

export const fetchOCPJobs = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });

    const params = dispatch(getRequestParams("ocp"));

    const response = await API.get(API_ROUTES.OCP_JOBS_API_V1, { params });

    if (response.status === 200) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_OCP_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_OCP_JOBS_DATA,
        payload: response.data.results,
      });

      dispatch(tableReCalcValues());
      dispatch({
        type: TYPES.SET_OCP_PAGE_TOTAL,
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

export const setOCPPage = (pageNo) => ({
  type: TYPES.SET_OCP_PAGE,
  payload: pageNo,
});

export const setOCPPageOptions = (page, perPage) => ({
  type: TYPES.SET_OCP_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const setOCPOffset = (offset) => ({
  type: TYPES.SET_OCP_OFFSET,
  payload: offset,
});

export const setOCPSortIndex = (index) => ({
  type: TYPES.SET_OCP_SORT_INDEX,
  payload: index,
});

export const setOCPSortDir = (direction) => ({
  type: TYPES.SET_OCP_SORT_DIR,
  payload: direction,
});

export const setOCPCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().ocp.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({ name: item, value: item }));

  dispatch({
    type: TYPES.SET_OCP_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_OCP_FILTER_OPTIONS,
    payload: list,
  });
};

export const applyFilters = () => (dispatch) => {
  dispatch(setOCPOffset(INITAL_OFFSET));
  dispatch(setOCPPage(START_PAGE));
  dispatch(fetchOCPJobs());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
};

export const setSelectedOCPFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().ocp.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_SELECTED_OCP_FILTERS,
    payload: selectedFilters,
  });
};
export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "ocp", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_SELECTED_OCP_FILTERS,
      payload: selectedFilters,
    });
  };
export const setOCPAppliedFilters = (navigate) => (dispatch, getState) => {
  const { start_date, end_date, selectedFilters } = getState().ocp;
  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_OCP_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const removeOCPAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "ocp")
    );
    const { start_date, end_date } = getState().ocp;
    dispatch({
      type: TYPES.SET_OCP_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const setOCPDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().ocp.appliedFilters;

    dispatch({
      type: TYPES.SET_OCP_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  };

export const applyOCPDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setOCPOffset(INITAL_OFFSET));
    dispatch(setOCPPage(START_PAGE));
    dispatch(setOCPDateFilter(start_date, end_date, navigate));
    dispatch(fetchOCPJobs());
    dispatch(buildFilterData());
  };
export const setOCPFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OCP_APPLIED_FILTERS,
  payload: searchParams,
});

export const setOCPOtherSummaryFilter = () => (dispatch, getState) => {
  const summary = getState().ocp.summary;
  if (summary?.othersCount !== 0) {
    dispatch(setSelectedFilter("jobStatus", OTHERS, false));
    dispatch(setOCPAppliedFilters());
  }
};

export const getOCPSummary = (countObj) => (dispatch) => {
  const summary = calculateSummary(countObj);
  dispatch({
    type: TYPES.SET_OCP_SUMMARY,
    payload: summary,
  });
};

export const fetchGraphData =
  (uuid, nodeName) => async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.GRAPH_LOADING });

      const graphData = getState().ocp.graphData;
      const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
      if (!hasData) {
        const response = await API.get(
          `${API_ROUTES.OCP_GRAPH_API_V1}/${uuid}`
        );

        if (response.status === 200) {
          dispatch({
            type: TYPES.SET_OCP_GRAPH_DATA,
            payload: { uuid, data: [[nodeName, response.data]] },
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

export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().ocp.tableColumns];
  const tableFilters = getState().ocp.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_OCP_COLUMNS,
    payload: tableColumns,
  });
};
export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ocp;

  dispatch(setOCPPageOptions(page, perPage));
};

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    const { tableFilters, categoryFilterValue } = getState().ocp;

    const params = dispatch(getRequestParams("ocp"));

    const response = await API.get(API_ROUTES.OCP_FILTERS_API_V1, { params });
    if (response.status === 200 && response?.data?.filterData?.length > 0) {
      dispatch(getOCPSummary(response.data.summary));
      dispatch({
        type: TYPES.SET_OCP_FILTER_DATA,
        payload: response.data.filterData,
      });
      const activeFilter = categoryFilterValue || tableFilters[0].name;
      dispatch(setOCPCatFilters(activeFilter));
    }
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
  }
};
