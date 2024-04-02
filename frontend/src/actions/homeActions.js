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
        type: TYPES.SET_OCP_JOBS_DATA,
        payload: response.data,
      });
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};
