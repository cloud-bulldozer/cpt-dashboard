import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";
import { appendQueryString } from "@/utils/helper";
import { showToast, showFailureToast } from "@/actions/toastActions";

export const fetchILabJobs = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date } = getState().ilab;
    const response = await API.get(API_ROUTES.ILABS_JOBS_API_V1, {
      params: {
        ...(start_date && { start_date }),
        ...(end_date && { end_date }),
      },
    });
    if (response.status === 200 && response?.data?.results.length > 0) {
      //   const startDate = new Date(response.data.startDate),
      //     endDate = new Date(response.data.endDate);
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      dispatch({
        type: TYPES.SET_ILAB_JOBS_DATA,
        payload: response.data.results,
      });
      //   dispatch({
      //     type: TYPES.SET_ILAB_DATE_FILTER,
      //     payload: {
      //       start_date: `${startDate.getFullYear()}-${startDate.getMonth()}-${startDate.getDate()}`,
      //       end_date: `${endDate.getFullYear()}-${endDate.getMonth()}-${endDate.getDate()}`,
      //     },
      //   });
      dispatch({
        type: TYPES.SET_ILAB_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });
    }
  } catch (error) {
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const setIlabDateFilter =
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

    dispatch(fetchILabJobs());
  };

export const fetchGraphData = (uid, metric) => async (dispatch) => {
  try {
    dispatch({ type: TYPES.GRAPH_LOADING });
    const periods = await API.get(`/api/v1/ilab/runs/${uid}/periods`);
    let graphs = [];
    periods.data.forEach((p) => {
      graphs.push({ metric, periods: [p.id] });
      graphs.push({
        metric: "mpstat::Busy-CPU",
        aggregate: true,
        periods: [p.id],
      });
    });
    const response = await API.post(`/api/v1/ilab/runs/multigraph`, {
      run: uid,
      name: metric,
      graphs,
    });
    if (response.status === 200) {
      dispatch({
        type: TYPES.SET_ILAB_GRAPH_DATA,
        payload: {
          uid,
          data: response.data.data,
          layout: response.data.layout,
        },
      });
    }
  } catch (error) {
    console.error(error);
    dispatch(showToast("danger", "Graph error", error.data));
  }
  dispatch({ type: TYPES.GRAPH_COMPLETED });
};
