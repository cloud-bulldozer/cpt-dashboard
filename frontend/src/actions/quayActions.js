import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper.js";

import API from "@/utils/axiosInstance";
import { showFailureToast } from "@/actions/toastActions";

export const fetchQuayJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
    const response = await API.get(API_ROUTES.QUAY_JOBS_API_V1, {
      params: {
        pretty: true,
        start_date: "2022-08-16",
        end_date: "2024-08-16",
        // ...(start_date && { start_date }),
        // ...(end_date && { end_date }),
      },
    });
    if (response?.data?.results?.length > 0) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      //on initial load startDate and endDate are empty, so from response append to url
      appendDateFilter(startDate, endDate);
      dispatch({
        type: TYPES.SET_QUAY_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_QUAY_FILTERED_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_QUAY_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
      dispatch(tableReCalcValues());
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const setQuayPage = (pageNo) => ({
  type: TYPES.SET_QUAY_PAGE,
  payload: pageNo,
});

export const setQuayPageOptions = (page, perPage) => ({
  type: TYPES.SET_QUAY_PAGE_OPTIONS,
  payload: { page, perPage },
});
export const setQuaySortIndex = (index) => ({
  type: TYPES.SET_QUAY_SORT_INDEX,
  payload: index,
});

export const setQuaySortDir = (direction) => ({
  type: TYPES.SET_QUAY_SORT_DIR,
  payload: direction,
});
export const sliceQuayTableRows =
  (startIdx, endIdx) => (dispatch, getState) => {
    const results = [...getState().quay.filteredResults];

    dispatch({
      type: TYPES.SET_QUAY_INIT_JOBS,
      payload: results.slice(startIdx, endIdx),
    });
  };
export const tableReCalcValues = () => (dispatch) => {
  dispatch(setQuayPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceQuayTableRows(0, DEFAULT_PER_PAGE));
};
