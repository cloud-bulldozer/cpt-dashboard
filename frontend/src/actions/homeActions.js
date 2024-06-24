import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper";
import { calculateMetrics, getFilteredData, sortTable } from "./commonActions";

import API from "@/utils/axiosInstance";
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
        // start_date: "2024-04-21",
        // end_date: "2024-04-22",
      },
    });
    if (response?.data?.results?.length > 0) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);

      dispatch({
        type: TYPES.SET_CPT_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_CPT_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
      dispatch(applyFilters());
      dispatch(sortTable("cpt"));
      dispatch(getCPTSummary());
      dispatch(setPageOptions(START_PAGE, DEFAULT_PER_PAGE));
      dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
      dispatch(buildFilterData());
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

export const sliceTableRows = (startIdx, endIdx) => (dispatch, getState) => {
  const results = [...getState().cpt.filteredResults];

  dispatch({
    type: TYPES.SET_CPT_INIT_JOBS,
    payload: results.slice(startIdx, endIdx),
  });
};

export const buildFilterData = () => (dispatch, getState) => {
  const results = [...getState().cpt.results];

  const tableFilters = [...getState().cpt.tableFilters];

  const filterData = [];
  for (const filter of tableFilters) {
    const key = filter.value;
    let obj = {
      name: filter.name,
      key,
      value: [...new Set(results.map((item) => item[key]))],
    };
    filterData.push(obj);
  }
  dispatch({
    type: TYPES.SET_CPT_FILTER_DATA,
    payload: filterData,
  });
  dispatch(setCatFilters(tableFilters[0].name));
};

export const setCatFilters = (category) => (dispatch, getState) => {
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

export const setAppliedFilters =
  (selectedOption, navigate) => (dispatch, getState) => {
    const { categoryFilterValue, filterData, start_date, end_date } =
      getState().cpt;
    const appliedFilters = { ...getState().cpt.appliedFilters };

    const category = filterData.filter(
      (item) => item.name === categoryFilterValue
    )[0].key;
    appliedFilters[category] = selectedOption;

    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const filterFromSummary =
  (category, value, navigate) => (dispatch, getState) => {
    const { start_date, end_date } = getState().cpt;
    const appliedFilters = { ...getState().cpt.appliedFilters };
    appliedFilters[category] = value;
    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };
export const setOtherSummaryFilter = () => (dispatch, getState) => {
  const filteredResults = [...getState().cpt.filteredResults];
  const keyWordArr = ["SUCCESS", "FAILURE"];
  const data = filteredResults.filter(
    (item) => !keyWordArr.includes(item.jobStatus)
  );
  dispatch({
    type: TYPES.SET_FILTERED_DATA,
    payload: data,
  });
  dispatch(getCPTSummary());
  dispatch(setPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
};
export const removeAppliedFilters =
  (filterKey, navigate) => (dispatch, getState) => {
    const appliedFilters = { ...getState().cpt.appliedFilters };
    const { start_date, end_date } = getState().cpt;
    const name = filterKey;
    // eslint-disable-next-line no-unused-vars
    const { [name]: removedProperty, ...remainingObject } = appliedFilters;

    dispatch({
      type: TYPES.SET_APPLIED_FILTERS,
      payload: remainingObject,
    });
    appendQueryString({ ...remainingObject, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyFilters = () => (dispatch, getState) => {
  const { appliedFilters } = getState().cpt;

  const results = [...getState().cpt.results];

  const isFilterApplied =
    Object.keys(appliedFilters).length > 0 &&
    !Object.values(appliedFilters).includes("");

  const filtered = getFilteredData(appliedFilters, results);

  dispatch({
    type: TYPES.SET_FILTERED_DATA,
    payload: isFilterApplied ? filtered : results,
  });
  dispatch(getCPTSummary());
  dispatch(setPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceTableRows(0, DEFAULT_PER_PAGE));
};

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_APPLIED_FILTERS,
  payload: searchParams,
});

export const setDateFilter =
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

export const setPage = (pageNo) => ({
  type: TYPES.SET_PAGE,
  payload: pageNo,
});

export const setPageOptions = (page, perPage) => ({
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
