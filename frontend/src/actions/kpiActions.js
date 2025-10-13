import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";
import { setLastUpdatedTime } from "./headerActions";

export const fetchKPIData = (beginDate, endDate) => async (dispatch) => {
  try {
    dispatch({ type: TYPES.SET_OCP_KPI_LOADING });

    const params = {};
    if (beginDate) params.start_date = beginDate;
    if (endDate) params.end_date = endDate;

    const response = await API.get(API_ROUTES.OCP_KPI_API_V1, { params });

    if (response.status === 200) {
      dispatch({
        type: TYPES.SET_OCP_KPI_DATA,
        payload: response.data,
      });
    }

    dispatch(setLastUpdatedTime());
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data,
      )}`,
    );
  }
  dispatch({ type: TYPES.SET_OCP_KPI_COMPLETED });
};

export const setKPIDateFilter = (startDate, endDate) => (dispatch) => {
  dispatch({
    type: TYPES.SET_OCP_KPI_DATE_FILTER,
    payload: {
      startDate,
      endDate,
    },
  });
};
