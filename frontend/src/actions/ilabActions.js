import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import { showFailureToast, showToast } from "@/actions/toastActions";

import API from "@/utils/axiosInstance";
import { appendQueryString } from "@/utils/helper";
import { cloneDeep } from "lodash";

export const fetchILabJobs = () => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const { start_date, end_date, size, offset } = getState().ilab;
    const response = await API.get(API_ROUTES.ILABS_JOBS_API_V1, {
      params: {
        ...(start_date && { start_date }),
        ...(end_date && { end_date }),
        ...(size && { size }),
        ...(offset && { offset }),
      },
    });
    if (response.status === 200 && response?.data?.results.length > 0) {
      const startDate = response.data.startDate,
        endDate = response.data.endDate;
      dispatch({
        type: TYPES.SET_ILAB_JOBS_DATA,
        payload: response.data.results,
      });

      dispatch({
        type: TYPES.SET_ILAB_DATE_FILTER,
        payload: {
          start_date: startDate,
          end_date: endDate,
        },
      });

      dispatch({
        type: TYPES.SET_ILAB_TOTAL_ITEMS,
        payload: response.data.total,
      });
      dispatch({
        type: TYPES.SET_ILAB_OFFSET,
        payload: response.data.next_offset,
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

export const fetchMetricsInfo = (uid) => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const response = await API.get(`/api/v1/ilab/runs/${uid}/metrics`);
    if (response.status === 200) {
      if (
        response.data.constructor === Object &&
        Object.keys(response.data).length > 0
      ) {
        dispatch({
          type: TYPES.SET_ILAB_METRICS,
          payload: { uid, metrics: Object.keys(response.data) },
        });
      }
    }
  } catch (error) {
    console.error(error);
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const fetchGraphData =
  (uid, metric, primary_metric) => async (dispatch, getState) => {
    try {
      const graphData = cloneDeep(getState().ilab.graphData);
      const filterData = graphData.filter((i) => i.uid !== uid);
      dispatch({
        type: TYPES.SET_ILAB_GRAPH_DATA,
        payload: filterData,
      });
      const copyData = cloneDeep(filterData);
      dispatch({ type: TYPES.GRAPH_LOADING });
      const periods = await API.get(`/api/v1/ilab/runs/${uid}/periods`);
      let graphs = [];
      periods.data.forEach((p) => {
        graphs.push({ metric: p.primary_metric, periods: [p.id] });
        graphs.push({
          metric,
          aggregate: true,
          periods: [p.id],
        });
      });
      const response = await API.post(`/api/v1/ilab/runs/multigraph`, {
        run: uid,
        name: primary_metric,
        graphs,
      });
      if (response.status === 200) {
        copyData.push({
          uid,
          data: response.data.data,
          layout: response.data.layout,
        });
        dispatch({
          type: TYPES.SET_ILAB_GRAPH_DATA,
          payload: copyData,
        });
      }
    } catch (error) {
      console.error(error);
      dispatch(showToast("danger", "Graph error", error.data));
    }
    dispatch({ type: TYPES.GRAPH_COMPLETED });
  };

export const setIlabPage = (pageNo) => ({
  type: TYPES.SET_ILAB_PAGE,
  payload: pageNo,
});

export const setIlabPageOptions = (page, perPage) => ({
  type: TYPES.SET_ILAB_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const checkIlabJobs = (newPage) => (dispatch, getState) => {
  const results = cloneDeep(getState().ilab.results);
  const { totalItems, perPage } = getState().ilab;

  const startIdx = (newPage - 1) * perPage;
  const endIdx = newPage * perPage;

  if (
    (typeof results[startIdx] === "undefined" ||
      typeof results[endIdx] === "undefined") &&
    results.length < totalItems
  ) {
    dispatch(fetchILabJobs());
  }
};

export const setSelectedMetrics = (id, metrics) => (dispatch, getState) => {
  const metrics_selected = cloneDeep(getState().ilab.metrics_selected);
  // if (id in metrics_selected) {
  //   metrics_selected[id] = metrics;
  // } else {
  //   metrics_selected[id] =  metrics;
  // }
  metrics_selected[id] = metrics;
  dispatch({
    type: TYPES.SET_ILAB_SELECTED_METRICS,
    payload: metrics_selected,
  });
};
