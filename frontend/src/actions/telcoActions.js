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

export const fetchTelcoJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().telco;
    const response = await API.get(API_ROUTES.TELCO_JOBS_API_V1, {
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
        type: TYPES.SET_TELCO_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_TELCO_FILTERED_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_TELCO_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
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

export const setTelcoSortDir = (direction) => ({
  type: TYPES.SET_TELCO_SORT_DIR,
  payload: direction,
});
export const sliceTelcoTableRows =
  (startIdx, endIdx) => (dispatch, getState) => {
    const results = [...getState().telco.filteredResults];

    dispatch({
      type: TYPES.SET_TELCO_INIT_JOBS,
      payload: results.slice(startIdx, endIdx),
    });
  };
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
export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().telco;

  const results = [...getState().telco.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    Object.values(appliedFilters).flat().length > 0;

  const filtered = isFilterApplied
    ? getFilteredData(appliedFilters, results)
    : results;

  dispatch({
    type: TYPES.SET_TELCO_FILTERED_DATA,
    payload: filtered,
  });
  dispatch(tableReCalcValues());
  dispatch(buildFilterData("telco"));
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

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().telco.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
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

    dispatch(fetchTelcoJobsData());
  };

export const getTelcoSummary = () => (dispatch, getState) => {
  const results = [...getState().telco.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_TELCO_SUMMARY,
    payload: countObj,
  });
};

export const setTelcoOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().telco.filteredResults];
  const keyWordArr = ["success", "failure"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  dispatch({
    type: TYPES.SET_TELCO_FILTERED_DATA,
    payload: data,
  });
  dispatch(tableReCalcValues());
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
  (uuid, encryption) => async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.GRAPH_LOADING });

      const graphData = getState().ocp.graphData;
      const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
      if (!hasData) {
        const response = await API.get(
          `${API_ROUTES.TELCO_GRAPH_API_V1}/${uuid}/${encryption}`
        );

        if (response.status === 200) {
          const result = Object.keys(response.data).map((key) => [
            key,
            response.data[key],
          ]);
          dispatch({
            type: TYPES.SET_TELCO_GRAPH_DATA,
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
  dispatch(getTelcoSummary());
  dispatch(setTelcoPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceTelcoTableRows(0, DEFAULT_PER_PAGE));
};
