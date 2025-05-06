import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";
import { appendQueryString } from "@/utils/helper";
import { cloneDeep } from "lodash";
import { showFailureToast } from "@/actions/toastActions";
import {
  INITAL_OFFSET,
  START_PAGE,
} from "@/assets/constants/paginationConstants";

export const fetchIlabJobs =
  (shouldStartFresh = false) =>
  async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.LOADING });
      const { start_date, end_date, size, offset, results } = getState().ilab;
      const response = await API.get(API_ROUTES.ILABS_JOBS_API_V1, {
        params: {
          ...(start_date && { start_date }),
          ...(end_date && { end_date }),
          ...(size && { size }),
          ...(offset && { offset }),
        },
      });
      if (response.status === 200) {
        const startDate = response.data.startDate,
          endDate = response.data.endDate;
        dispatch({
          type: TYPES.SET_ILAB_JOBS_DATA,
          payload: shouldStartFresh
            ? response.data.results
            : [...results, ...response.data.results],
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

        dispatch(tableReCalcValues());
      }
    } catch (error) {
      dispatch(showFailureToast());
    }
    dispatch({ type: TYPES.COMPLETED });
  };

export const applyFilters = () => (dispatch) => {
  dispatch(setIlabOffset(INITAL_OFFSET));
  dispatch(setIlabPage(START_PAGE));
  dispatch(fetchIlabJobs());
  dispatch(buildFilterData());
  dispatch(tableReCalcValues());
};

export const setIlabDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().ilab.appliedFilters;

    dispatch({
      type: TYPES.SET_ILAB_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  };

export const removeIlabAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const applyIlabDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setIlabOffset(INITAL_OFFSET));
    dispatch(setIlabPage(START_PAGE));
    dispatch(setIlabDateFilter(start_date, end_date, navigate));
    dispatch(fetchIlabJobs());
  };

export const setIlabCatFilters = (category) => (dispatch, getState) => {};

export const setIlabAppliedFilters = (navigate) => (dispatch, getState) => {};

export const setIlabOtherSummaryFilter = () => (dispatch, getState) => {};

export const setIlabPage = (pageNo) => ({
  type: TYPES.SET_ILAB_PAGE,
  payload: pageNo,
});

export const setIlabOffset = (offset) => ({
  type: TYPES.SET_ILAB_OFFSET,
  payload: offset,
});

export const setIlabPageOptions = (page, perPage) => ({
  type: TYPES.SET_ILAB_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ilab;

  dispatch(setIlabPageOptions(page, perPage));
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

export const fetchPeriods = (uid) => async (dispatch) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const response = await API.get(`/api/v1/ilab/runs/${uid}/periods`);
    if (response.status === 200) {
      dispatch({
        type: TYPES.SET_ILAB_PERIODS,
        payload: { uid, periods: response.data },
      });
    }
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const fetchGraphData =
  (uid, metric, primary_metric) => async (dispatch, getState) => {
    try {
      const periods = getState().ilab.periods.find((i) => i.uid == uid);
      const graphData = cloneDeep(getState().ilab.graphData);
      const filterData = graphData.filter((i) => i.uid !== uid);
      dispatch({
        type: TYPES.SET_ILAB_GRAPH_DATA,
        payload: filterData,
      });
      const copyData = cloneDeep(filterData);
      dispatch({ type: TYPES.GRAPH_LOADING });
      let graphs = [];
      periods?.periods?.forEach((p) => {
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
      console.error(
        `ERROR (${error?.response?.status}): ${JSON.stringify(
          error?.response?.data
        )}`
      );
      dispatch(showFailureToast());
    }
    dispatch({ type: TYPES.GRAPH_COMPLETED });
  };

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
    dispatch(fetchIlabJobs());
  }
};

export const setSelectedMetrics = (id, metrics) => (dispatch, getState) => {
  const metrics_selected = cloneDeep(getState().ilab.metrics_selected);
  metrics_selected[id] = metrics;
  dispatch({
    type: TYPES.SET_ILAB_SELECTED_METRICS,
    payload: metrics_selected,
  });
};
