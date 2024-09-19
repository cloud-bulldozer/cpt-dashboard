import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper";
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
import { showFailureToast } from "@/actions/toastActions";

export const fetchOCPJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
    const response = await API.get(API_ROUTES.CPT_JOBS_API_V1, {
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
        type: TYPES.SET_CPT_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }

    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_CPT_JOBS_DATA,
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

export const setCPTSortIndex = (index) => ({
  type: TYPES.SET_CPT_SORT_INDEX,
  payload: index,
});

export const setCPTSortDir = (direction) => ({
  type: TYPES.SET_CPT_SORT_DIR,
  payload: direction,
});

export const sliceCPTTableRows = (startIdx, endIdx) => (dispatch, getState) => {
  const results = [...getState().cpt.filteredResults];

  dispatch({
    type: TYPES.SET_CPT_INIT_JOBS,
    payload: results.slice(startIdx, endIdx),
  });
};

export const setCPTCatFilters = (category) => (dispatch, getState) => {
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

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().cpt.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_SELECTED_FILTERS,
    payload: selectedFilters,
  });
};
export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "cpt", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_SELECTED_FILTERS,
      payload: selectedFilters,
    });
  };

export const setCPTAppliedFilters = (navigate) => (dispatch, getState) => {
  const { selectedFilters, start_date, end_date } = getState().cpt;

  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const setCPTOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().cpt.filteredResults];
  const keyWordArr = ["success", "failure"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  dispatch({
    type: TYPES.SET_FILTERED_DATA,
    payload: data,
  });
  dispatch(tableReCalcValues());
};
export const removeCPTAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const { start_date, end_date } = getState().cpt;

    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "cpt")
    );

    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().cpt;

  const results = [...getState().cpt.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    Object.values(appliedFilters).flat().length > 0;

  const filtered = isFilterApplied
    ? getFilteredData(appliedFilters, results)
    : results;

  dispatch({
    type: TYPES.SET_FILTERED_DATA,
    payload: filtered,
  });
  dispatch(tableReCalcValues());
  dispatch(buildFilterData("cpt"));
};

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_APPLIED_FILTERS,
  payload: searchParams,
});

export const setCPTDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().cpt.appliedFilters;

    dispatch({
      type: TYPES.SET_CPT_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);

    dispatch(fetchOCPJobsData());
  };

export const setCPTPage = (pageNo) => ({
  type: TYPES.SET_PAGE,
  payload: pageNo,
});

export const setCPTPageOptions = (page, perPage) => ({
  type: TYPES.SET_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const getCPTSummary = () => (dispatch, getState) => {
  const results = [...getState().cpt.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_CPT_SUMMARY,
    payload: countObj,
  });
};

export const tableReCalcValues = () => (dispatch) => {
  dispatch(getCPTSummary());
  dispatch(setCPTPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceCPTTableRows(0, DEFAULT_PER_PAGE));
};
