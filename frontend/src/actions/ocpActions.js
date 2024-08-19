import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

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
  sortTable,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { showFailureToast } from "./toastActions";

export const fetchOCPJobs = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().ocp;
    const response = await API.get(API_ROUTES.OCP_JOBS_API_V1, {
      params: {
        pretty: true,
        ...(start_date && { start_date }),
        ...(end_date && { end_date }),
      },
    });
    if (response?.data?.results?.length > 0) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_OCP_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_OCP_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
      dispatch(applyFilters());
      dispatch(sortTable("ocp"));
      dispatch(tableReCalcValues());
    }
  } catch (error) {
    dispatch(showFailureToast());
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

export const sliceOCPTableRows = (startIdx, endIdx) => (dispatch, getState) => {
  const results = [...getState().ocp.filteredResults];

  dispatch({
    type: TYPES.SET_OCP_INIT_JOBS,
    payload: results.slice(startIdx, endIdx),
  });
};

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

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().ocp;

  const results = [...getState().ocp.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    !Object.values(appliedFilters).includes("");

  const filtered = isFilterApplied
    ? getFilteredData(appliedFilters, results)
    : results;

  dispatch({
    type: TYPES.SET_OCP_FILTERED_DATA,
    payload: filtered,
  });
  dispatch(tableReCalcValues());
  dispatch(buildFilterData("ocp"));
};

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
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

    dispatch(fetchOCPJobs());
  };

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OCP_APPLIED_FILTERS,
  payload: searchParams,
});

export const setOCPOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().ocp.filteredResults];
  const keyWordArr = ["success", "failure"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  dispatch({
    type: TYPES.SET_OCP_FILTERED_DATA,
    payload: data,
  });
  dispatch(tableReCalcValues());
};

export const getOCPSummary = () => (dispatch, getState) => {
  const results = [...getState().ocp.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_OCP_SUMMARY,
    payload: countObj,
  });
};

export const fetchGraphData = (uuid) => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.GRAPH_LOADING });

    const graphData = getState().ocp.graphData;
    const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
    if (!hasData) {
      const response = await API.get(`${API_ROUTES.OCP_GRAPH_API_V1}/${uuid}`);

      if (response.status === 200) {
        dispatch({
          type: TYPES.SET_OCP_GRAPH_DATA,
          payload: { uuid, data: response.data },
        });
      }
    }
  } catch (error) {
    dispatch(showFailureToast());
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
export const tableReCalcValues = () => (dispatch) => {
  dispatch(getOCPSummary());
  dispatch(setOCPPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceOCPTableRows(0, DEFAULT_PER_PAGE));
};
