import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";
import { appendQueryString } from "@/utils/helper";
import { cloneDeep } from "lodash";
import { showFailureToast } from "@/actions/toastActions";

export const fetchILabJobs =
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
      if (response.status === 200 && response?.data?.results.length > 0) {
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
export const sliceIlabTableRows =
  (startIdx, endIdx) => (dispatch, getState) => {
    const results = [...getState().ilab.results];

    dispatch({
      type: TYPES.SET_ILAB_INIT_JOBS,
      payload: results.slice(startIdx, endIdx),
    });
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

export const fetchMetricsInfo = (uid) => async (dispatch, getState) => {
  try {
    if (getState().ilab.metrics?.find((i) => i.uid == uid)) {
      return;
    }
    dispatch({ type: TYPES.LOADING });
    const response = await API.get(`/api/v1/ilab/runs/${uid}/metrics`);
    if (response.status === 200) {
      if (
        response.data.constructor === Object &&
        Object.keys(response.data).length > 0
      ) {
        const metrics = Object.keys(response.data).sort();
        dispatch({
          type: TYPES.SET_ILAB_METRICS,
          payload: { uid, metrics },
        });
      }
    }
  } catch (error) {
    console.error(error);
    dispatch(showFailureToast());
  }
  dispatch({ type: TYPES.COMPLETED });
};

export const fetchPeriods = (uid) => async (dispatch, getState) => {
  try {
    if (getState().ilab.periods?.find((i) => i.uid == uid)) {
      return;
    }
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

export const fetchSummaryData = (uid) => async (dispatch, getState) => {
  try {
    const periods = getState().ilab.periods.find((i) => i.uid == uid);
    const metrics = getState().ilab.metrics_selected;
    const avail_metrics = getState().ilab.metrics;
    dispatch({ type: TYPES.SET_ILAB_SUMMARY_LOADING });
    let summaries = [];
    periods?.periods?.forEach((p) => {
      if (p.is_primary) {
        summaries.push({
          run: uid,
          metric: p.primary_metric,
          periods: [p.id],
        });
      }
      if (metrics) {
        metrics.forEach((metric) => {
          if (
            avail_metrics.find((m) => m.uid == uid)?.metrics?.includes(metric)
          ) {
            summaries.push({
              run: uid,
              metric,
              aggregate: true,
              periods: [p.id],
            });
          }
        });
      }
    });
    const response = await API.post(
      `/api/v1/ilab/runs/multisummary`,
      summaries
    );
    if (response.status === 200) {
      dispatch({
        type: TYPES.SET_ILAB_SUMMARY_DATA,
        payload: { uid, data: response.data },
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
  dispatch({ type: TYPES.SET_ILAB_SUMMARY_COMPLETE });
};

export const handleSummaryData = (uids) => async (dispatch, getState) => {
  try {
    const periods = getState().ilab.periods;
    const pUids = periods.map((i) => i.uid);
    const missingPeriods = uids.filter(function (x) {
      return pUids.indexOf(x) < 0;
    });
    await Promise.all(
      missingPeriods.map(async (uid) => {
        await dispatch(fetchPeriods(uid)); // Dispatch each item
      })
    );
    await Promise.all(
      uids.map(async (uid) => {
        await dispatch(fetchSummaryData(uid));
      })
    );
  } catch (error) {
    console.error(`ERROR: ${JSON.stringify(error)}`);
    dispatch(showFailureToast());
  }
};

export const fetchGraphData = (uid) => async (dispatch, getState) => {
  try {
    const periods = getState().ilab.periods.find((i) => i.uid == uid);
    const graphData = cloneDeep(getState().ilab.graphData);
    const filterData = graphData.filter((i) => i.uid !== uid);
    const metrics = getState().ilab.metrics_selected;
    const avail_metrics = getState().ilab.metrics;
    dispatch({
      type: TYPES.SET_ILAB_GRAPH_DATA,
      payload: filterData,
    });
    const copyData = cloneDeep(filterData);
    dispatch({ type: TYPES.GRAPH_LOADING });
    let graphs = [];
    periods?.periods?.forEach((p) => {
      if (p.is_primary) {
        graphs.push({ run: uid, metric: p.primary_metric, periods: [p.id] });
      }
      if (metrics) {
        metrics.forEach((metric) => {
          if (
            avail_metrics.find((m) => m.uid == uid)?.metrics?.includes(metric)
          ) {
            graphs.push({
              run: uid,
              metric,
              aggregate: true,
              periods: [p.id],
            });
          }
        });
      }
    });
    const response = await API.post(`/api/v1/ilab/runs/multigraph`, {
      name: `graph ${uid}`,
      graphs,
    });
    if (response.status === 200) {
      response.data.layout["width"] = 1500;
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

export const handleMultiGraph = (uids) => async (dispatch, getState) => {
  try {
    const periods = getState().ilab.periods;
    const pUids = periods.map((i) => i.uid);

    const missingPeriods = uids.filter(function (x) {
      return pUids.indexOf(x) < 0;
    });

    await Promise.all(
      missingPeriods.map(async (uid) => {
        await dispatch(fetchPeriods(uid)); // Dispatch each item
      })
    );

    dispatch(fetchMultiGraphData(uids));
  } catch (error) {
    console.error(
      `ERROR (${error?.response?.status}): ${JSON.stringify(
        error?.response?.data
      )}`
    );
    dispatch(showFailureToast());
  }
};
export const fetchMultiGraphData = (uids) => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const periods = getState().ilab.periods;
    const filterPeriods = periods.filter((item) => uids.includes(item.uid));
    const get_metrics = getState().ilab.metrics_selected;
    const avail_metrics = getState().ilab.metrics;

    let graphs = [];
    uids.forEach(async (uid) => {
      const periods = filterPeriods.find((i) => i.uid == uid);
      periods?.periods?.forEach((p) => {
        if (p.is_primary) {
          graphs.push({
            run: uid,
            metric: p.primary_metric,
            periods: [p.id],
          });
        }
        if (get_metrics) {
          get_metrics.forEach((metric) => {
            if (
              avail_metrics.find((m) => m.uid == uid)?.metrics?.includes(metric)
            ) {
              graphs.push({
                run: uid,
                metric,
                aggregate: true,
                periods: [p.id],
              });
            }
          });
        }
      });
    });
    console.log(graphs);
    const response = await API.post(`/api/v1/ilab/runs/multigraph`, {
      name: "comparison",
      relative: true,
      absolute_relative: true,
      graphs,
    });
    if (response.status === 200) {
      response.data.layout["width"] = 1500;
      const graphData = [];
      graphData.push({
        data: response.data.data,
        layout: response.data.layout,
      });
      dispatch({
        type: TYPES.SET_ILAB_MULTIGRAPH_DATA,
        payload: graphData,
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

export const toggleSelectedMetric = (metric) => (dispatch, getState) => {
  let metrics_selected = getState().ilab.metrics_selected;
  if (metrics_selected.includes(metric)) {
    metrics_selected = metrics_selected.filter((m) => m !== metric);
  } else {
    metrics_selected = [...metrics_selected, metric];
  }
  dispatch({
    type: TYPES.SET_ILAB_SELECTED_METRICS,
    payload: metrics_selected,
  });
};

export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ilab;

  const startIdx = page !== 1 ? (page - 1) * perPage : 0;
  const endIdx = page !== 1 ? page * perPage - 1 : perPage;
  dispatch(sliceIlabTableRows(startIdx, endIdx));
  dispatch(getMetaRowdId());
};

export const getMetaRowdId = () => (dispatch, getState) => {
  const tableData = getState().ilab.tableData;
  const metaId = tableData.map((item) => `metadata-toggle-${item.id}`);
  dispatch(setMetaRowExpanded(metaId));
};
export const toggleComparisonSwitch = () => ({
  type: TYPES.TOGGLE_COMPARISON_SWITCH,
});

export const setMetaRowExpanded = (expandedItems) => ({
  type: TYPES.SET_EXPANDED_METAROW,
  payload: expandedItems,
});