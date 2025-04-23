import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";
import API from "@/utils/axiosInstance";
import { showFailureToast } from "./toastActions.js";

export const setLastUpdatedTime = () => ({
  type: TYPES.SET_LAST_UPDATED_TIME,
  payload: new Date().toLocaleString().replace(", ", " ").toString(),
});

export const fetchAggregatorVersion = () => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const response = await API.get(API_ROUTES.AGG_VERSION_API);

    if (response.status === 200) {
      dispatch({
        type: TYPES.SET_AGGREGATOR_VERSION,
        payload: response?.data
      });
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};
