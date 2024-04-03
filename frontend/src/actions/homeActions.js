import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "@/actions/types.js";

import API from "@/utils/axiosInstance";
import { showFailureToast } from "@/actions/toastActions";

export const fetchOCPJobsData = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().cpt;
    const response = await API.get(API_ROUTES.CPT_JOBS_API_V1, {
      params: {
        pretty: true,
        ...(start_date && start_date),
        ...(end_date && end_date),
      },
    });
    if (response?.data?.results?.length > 0) {
      dispatch({
        type: TYPES.SET_CPT_JOBS_DATA,
        payload: response.data.results,
      });
      dispatch({
        type: TYPES.SET_CPT_DATE_FILTER,
        payload: {
          start_date: response.data.startDate,
          end_date: response.data.endDate,
        },
      });
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

const getSortableRowValues = (result, tableColumns) => {
  const tableKeys = tableColumns.map((item) => item.value);
  return tableKeys.map((key) => result[key]);
};

export const sortTable = () => (dispatch, getState) => {
  const { results, activeSortDir, activeSortIndex, tableColumns } =
    getState().cpt;

  if (activeSortIndex) {
    const sortedResults = results.sort((a, b) => {
      const aValue = getSortableRowValues(a, tableColumns)[activeSortIndex];
      const bValue = getSortableRowValues(b, tableColumns)[activeSortIndex];
      if (typeof aValue === "number") {
        if (activeSortDir === "asc") {
          return aValue - bValue;
        }
        return bValue - aValue;
      } else {
        if (activeSortDir === "asc") {
          return aValue.localeCompare(bValue);
        }
        return bValue.localeCompare(aValue);
      }
    });
    dispatch({
      type: TYPES.SET_CPT_JOBS_DATA,
      payload: sortedResults,
    });
  }
};

export const setCPTSortIndex = (index) => ({
  type: TYPES.SET_CPT_SORT_INDEX,
  payload: index,
});

export const setCPTSortDir = (direction) => ({
  type: TYPES.SET_CPT_SORT_DIR,
  payload: direction,
});
