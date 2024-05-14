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
  getFilteredData,
  sortTable,
} from "@/actions/commonActions.js";

import API from "@/utils/axiosInstance";
import { getAppliedFilters } from "./commonActions";
import { showFailureToast } from "@/actions/toastActions";

export const fetchOCPJobs = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
    const response = await API.get(API_ROUTES.OCP_JOBS_API_V1, {
      params: {
        pretty: true,
        ...(start_date && { start_date }),
        ...(end_date && { end_date }),
        // start_date: "2024-04-21",
        // end_date: "2024-04-22",
      },
    });
    if (response?.data?.results?.length > 0) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter();

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
      dispatch(setPageOptions(START_PAGE, DEFAULT_PER_PAGE));
      dispatch(sliceOCPTableRows(0, DEFAULT_PER_PAGE));
      dispatch(buildFilterData("ocp"));
      dispatch(getOCPSummary());
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const setPage = (pageNo) => ({
  type: TYPES.SET_OCP_PAGE,
  payload: pageNo,
});

export const setPageOptions = (page, perPage) => ({
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

  const filtered = getFilteredData(appliedFilters, results);

  dispatch({
    type: TYPES.SET_OCP_FILTERED_DATA,
    payload: isFilterApplied ? filtered : results,
  });
  dispatch(getOCPSummary());
  dispatch(setPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceOCPTableRows(0, DEFAULT_PER_PAGE));
};

export const setAppliedFilters =
  (selectedOption, navigate) => (dispatch, getState) => {
    const appliedFilters = dispatch(getAppliedFilters("ocp", selectedOption));
    const { start_date, end_date } = getState().ocp;
    dispatch({
      type: TYPES.SET_OCP_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const removeAppliedFilters =
  (filterKey, navigate) => (dispatch, getState) => {
    const appliedFilters = { ...getState().ocp.appliedFilters };
    const { start_date, end_date } = getState().ocp;
    const name = filterKey;
    // eslint-disable-next-line no-unused-vars
    const { [name]: removedProperty, ...remainingObject } = appliedFilters;

    dispatch({
      type: TYPES.SET_OCP_APPLIED_FILTERS,
      payload: remainingObject,
    });
    appendQueryString({ ...remainingObject, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const setDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().cpt.appliedFilters;

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

export const getOCPSummary = () => (dispatch, getState) => {
  const results = [...getState().ocp.filteredResults];

  const countObj = calculateMetrics(results);
  dispatch({
    type: TYPES.SET_OCP_SUMMARY,
    payload: countObj,
  });
};
