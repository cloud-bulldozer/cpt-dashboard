import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper.js";

import API from "@/utils/axiosInstance";
import { showFailureToast } from "@/actions/toastActions";

export const fetchTelcoJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
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
export const tableReCalcValues = () => (dispatch) => {
  dispatch(setTelcoPageOptions(START_PAGE, DEFAULT_PER_PAGE));
  dispatch(sliceTelcoTableRows(0, DEFAULT_PER_PAGE));
};
