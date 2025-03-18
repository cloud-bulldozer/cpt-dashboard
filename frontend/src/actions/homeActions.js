import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import { appendDateFilter, appendQueryString } from "@/utils/helper";
import {
  deleteAppliedFilters,
  getRequestParams,
  getSelectedFilter,
} from "./commonActions";

import API from "@/utils/axiosInstance";
import { INITAL_OFFSET } from "@/assets/constants/paginationConstants";
import { setLastUpdatedTime } from "./headerActions";
import { showFailureToast } from "@/actions/toastActions";

const getCloneDeep = async () => (await import("lodash/cloneDeep")).default;

export const fetchOCPJobsData =
  (isNewSearch = false) =>
  async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.LOADING });

      const params = dispatch(getRequestParams("cpt"));
      const results = getState().cpt.results;
      params["totalJobs"] = getState().cpt.totalJobs;
      const response = await API.get(API_ROUTES.CPT_JOBS_API_V1, { params });
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
          payload: isNewSearch
            ? response.data.results
            : [...results, ...response.data.results],
        });
        dispatch({
          type: TYPES.SET_CPT_PAGE_TOTAL,
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

export const setCPTSortIndex = (index) => ({
  type: TYPES.SET_CPT_SORT_INDEX,
  payload: index,
});

export const setCPTSortDir = (direction) => ({
  type: TYPES.SET_CPT_SORT_DIR,
  payload: direction,
});

export const setCPTOffset = (offset) => ({
  type: TYPES.SET_CPT_OFFSET,
  payload: offset,
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

export const setSelectedFilterFromUrl =
  (params) => async (dispatch, getState) => {
    const cloneDeep = await getCloneDeep();
    const selectedFilters = cloneDeep(getState().cpt.selectedFilters);
    for (const key in params) {
      selectedFilters.find((i) => i.name === key).value =
        params[key].split(",");
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

export const applyFilters = () => (dispatch) => {
  dispatch(setCPTOffset(INITAL_OFFSET));
  dispatch(fetchOCPJobsData(true));
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
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
  };

export const applyCPTDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setCPTOffset(INITAL_OFFSET));
    dispatch(setCPTDateFilter(start_date, end_date, navigate));
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

export const getCPTSummary = (countObj) => (dispatch) => {
  const other = countObj["other"]
    ? countObj["other"]
    : countObj["total"] -
      ((countObj["success"] || 0) + (countObj["failure"] || 0));
  const summary = {
    othersCount: other,
    successCount: countObj["success"] || 0,
    failureCount: countObj["failure"] || 0,
    total: countObj["total"],
  };
  dispatch({
    type: TYPES.SET_CPT_SUMMARY,
    payload: summary,
  });
};

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().cpt;
  dispatch(setCPTPageOptions(page, perPage));
  const startIdx = page !== 0 ? (page - 1) * perPage : 0;
  const endIdx = startIdx + perPage - 1;
  dispatch(sliceCPTTableRows(startIdx, endIdx));
};

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { tableFilters, categoryFilterValue } = getState().ocp;

    const params = dispatch(getRequestParams("cpt"));

    const response = await API.get(API_ROUTES.CPT_FILTERS_API_V1, { params });

    if (response.status !== 200 || !response.data?.filterData?.length) {
      console.warn("No filter data received from API");
      dispatch(getCPTSummary({}));
      dispatch({ type: TYPES.SET_CPT_FILTER_DATA, payload: [] });
      return;
    }

    const { summary, filterData } = response.data;

    dispatch(getCPTSummary(summary));
    dispatch({ type: TYPES.SET_CPT_FILTER_DATA, payload: filterData });

    const defaultCategory = categoryFilterValue || tableFilters?.[0]?.name;
    dispatch(setCPTCatFilters(defaultCategory));
  } catch (error) {
    console.error("Error fetching filter data:", error);
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const fetchDataConcurrently = () => async (dispatch) => {
  try {
    await Promise.all([
      dispatch(buildFilterData()),
      dispatch(fetchOCPJobsData()),
    ]);
  } catch (error) {
    dispatch(showFailureToast());
  }
};
