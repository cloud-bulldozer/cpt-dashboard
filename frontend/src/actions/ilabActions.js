import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import {
  INITAL_OFFSET,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import { appendDateFilter, appendQueryString } from "@/utils/helper";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { showFailureToast } from "@/actions/toastActions";

/**
 * Fetch and store InstructLab jobs based on configured filters.
 *
 * @param {boolean} [shouldStartFresh=false]
 */
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
        const startDate = new Date(response.data.startDate),
          endDate = new Date(response.data.endDate);
        dispatch({
          type: TYPES.SET_ILAB_JOBS_DATA,
          payload: shouldStartFresh
            ? response.data.results
            : [...results, ...response.data.results],
        });
        const start_date = startDate.toISOString().split("T")[0],
          end_date = endDate.toISOString().split("T")[0];

        dispatch({
          type: TYPES.SET_ILAB_DATE_FILTER,
          payload: {
            start_date,
            end_date,
          },
        });

        appendDateFilter(start_date, end_date);
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

/**
 * Apply current filters
 */
export const applyFilters = () => (dispatch) => {
  dispatch(setIlabOffset(INITAL_OFFSET));
  dispatch(setIlabPage(START_PAGE));
  dispatch(fetchIlabJobs());
  dispatch(tableReCalcValues());
};

/**
 * Store the start & end date filters in redux and as URL
 * query parameters for page reload.
 *
 * @param {string} start_date
 * @param {string} end_date
 * @param {React NavigateFunction} navigate
 */
export const setIlabDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch({
      type: TYPES.SET_ILAB_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });
    dispatch(updateURL(navigate));
  };

/**
 * Set the category filters.
 *
 * TODO: currently unimplemented/unused for ILAB
 *
 * @param {string} category
 */
export const setIlabCatFilters = () => () => {};

/**
 * Set applied filters.
 *
 * TODO: currently unimplemented/unused for ILAB
 *
 * @param {function} navigate hook
 */
export const setIlabAppliedFilters = () => () => {};

/**
 * Set summery filters for non-[success|failure]
 *
 * TODO: currently unimplemented/unused for ILAB
 *
 * @param {string} category
 */
export const setIlabOtherSummaryFilter = () => () => {};

/**
 * Store the current page number for page fetch.
 *
 * @param {number} pageNo
 */
export const setIlabPage = (pageNo) => ({
  type: TYPES.SET_ILAB_PAGE,
  payload: pageNo,
});

/**
 * Store the current page offset for page fetch.
 *
 * @param {number} offset
 */
export const setIlabOffset = (offset) => ({
  type: TYPES.SET_ILAB_OFFSET,
  payload: offset,
});

/**
 * Store an updated page size and page number.
 *
 * @param {number} page
 * @param {number} perPage
 */
export const setIlabPageOptions = (page, perPage) => ({
  type: TYPES.SET_ILAB_PAGE_OPTIONS,
  payload: { page, perPage },
});

/**
 * Thunk to update page options
 */
export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ilab;

  dispatch(setIlabPageOptions(page, perPage));
};

/**
 * Remove applied filters
 *
 * @param {*} filterKey
 * @param {*} filterValue
 * @param {*} navigate
 */
export const removeIlabAppliedFilters = () => (dispatch) => {
  dispatch(applyFilters());
};

/**
 * Apply a new date filter, resetting pagination
 *
 * @param {*} start_date
 * @param {*} end_date
 * @param {*} navigate
 */
export const applyIlabDateFilter =
  (start_date, end_date, navigate) => (dispatch) => {
    dispatch(setIlabOffset(INITAL_OFFSET));
    dispatch(setIlabPage(START_PAGE));
    dispatch(setIlabDateFilter(start_date, end_date, navigate));
    dispatch(fetchIlabJobs());
  };

/**
 * Fetch the set of possible InstructLab run filters and store them.
 */
export const fetchIlabFilters = () => async (dispatch) => {
  try {
    const response = await API.get(`/api/v1/ilab/runs/filters`);
    dispatch({ type: TYPES.SET_ILAB_RUN_FILTERS, payload: response.data });
  } catch (error) {
    console.error(error);
    dispatch(showFailureToast());
  }
};

/**
 * Fetch the recorded metrics for a specific run and store them.
 *
 * @param {string} uid of a run
 */
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

/**
 * Fetch the recording periods for a specific run and store them.
 *
 * @param {string} uid of a run
 */
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

/**
 * Construct a metric title based on the metric template store.
 *
 * @param {string} uid of a run
 * @returns {string} metric title based on the template
 */
const makeTitle = (run, period, metric, template) => {
  if (!template) {
    return null;
  }
  try {
    const chip = /<((?<section>\w+):)?(?<name>\w+)>/;
    const params = run?.iterations?.find(
      (i) => i.iteration === period.iteration
    )?.params;
    let title = "";
    for (const t of template) {
      const ctx = chip.exec(t);
      if (ctx !== null) {
        const section = ctx.groups.section;
        const name = ctx.groups.name;
        if (!section) {
          if (name === "metric") {
            title += metric;
          } else if (name == "iteration") {
            title += period.iteration;
          } else if (name === "period") {
            title += period.name;
          }
        } else if (section === "run") {
          title += run?.[name] || t;
        } else if (section === "param") {
          title += params?.[name] || t;
        } else if (section === "tag") {
          title += run.tags?.[name] || t;
        } else {
          title += `<unkn ${t}>`;
        }
      } else {
        title += t;
      }
    }
    return title;
  } catch (e) {
    console.error(e);
    throw e;
  }
};

/**
 * Fetch and store metric statistics for a run.
 *
 * This will iterate through all defined recording periods for the run,
 * generating for each a request for statistics for each specified metric
 * within the period's time range. In addition, each "primary period" will
 * include a request for the period's "primary metric".
 *
 * To maximize store effectiveness, we store data for each run separately,
 * and combine data from multiple runs in the comparison table as needed
 * rather than combining runs in a single request.
 *
 * NOTE: we don't try to avoid a duplicate fetch operation for statistics
 * because the API call depends on the set of metrics selected and not just
 * the selected run.
 *
 * @param {string} uid of a run
 * @param {boolean} [useTemplate=false]
 */
export const fetchSummaryData =
  (uid, useTemplate = false) =>
  async (dispatch, getState) => {
    try {
      const run = getState().ilab.results.find((i) => i.id == uid);
      const template = useTemplate ? getState().ilab.metricTemplate : null;
      const periods = getState().ilab.periods.find((i) => i.uid == uid);
      const metrics = dispatch(getSelectedMetrics(uid));
      const avail_metrics = getState().ilab.metrics;
      dispatch({ type: TYPES.SET_ILAB_SUMMARY_LOADING });
      let summaries = [];
      periods?.periods?.forEach((p) => {
        if (p.is_primary) {
          summaries.push({
            run: uid,
            metric: p.primary_metric,
            periods: [p.id],
            title: makeTitle(run, p, p.primary_metric, template),
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
                title: makeTitle(run, p, metric, template),
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

/**
 * A helper to ensure that statistical summary data is available for a
 * selected set of runs. In general we should expect that all periods have
 * been fetched, but we make sure of that before fetching summary data for
 * all specified runs.
 *
 * @param {Array[string]} run uids
 */
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
        await dispatch(fetchSummaryData(uid, true));
      })
    );
  } catch (error) {
    console.error(`ERROR: ${JSON.stringify(error)}`);
    dispatch(showFailureToast());
  }
};

/**
 * Fetch and store Plotly graph data for a specified run.
 *
 * This will iterate through all defined recording periods for the run,
 * generating for each a graph request for each specified metric
 * within the period's time range. In addition, each "primary period" will
 * include a graph request for the period's "primary metric".
 *
 * @param {string} run uid
 * @returns {(dispatch: any, getState: any) => any}
 */
export const fetchGraphData = (uid) => async (dispatch, getState) => {
  try {
    const periods = getState().ilab.periods.find((i) => i.uid == uid);
    const graphData = cloneDeep(getState().ilab.graphData);
    const filterData = graphData.filter((i) => i.uid !== uid);
    const metrics = dispatch(getSelectedMetrics(uid));
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
        graphs.push({
          run: uid,
          metric: p.primary_metric,
          aggregate: true,
          periods: [p.id],
        });
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

/**
 * A helper to ensure that graph data is available for a selected set of
 * runs. In general we should expect that all periods have been fetched, but
 * we make sure of that before fetching graph data for all specified runs.
 *
 * @param {Array[string]} run uids
 */
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

/**
 * Generate a single Plotly graph containing potentially multiple metrics from
 * all periods of a set of runs.
 *
 * For each run, we iterate through the collection periods, generating a graph
 * for each selected metric over that period's time range. For each "primary
 * period" we also generate a graph for that period's "primary metric".
 *
 * @param {Array[string]} run uids
 */
export const fetchMultiGraphData = (uids) => async (dispatch, getState) => {
  try {
    dispatch({ type: TYPES.LOADING });
    const periods = getState().ilab.periods;
    const filterPeriods = periods.filter((item) => uids.includes(item.uid));
    const get_metrics = getState().ilab.metrics_selected;
    const avail_metrics = getState().ilab.metrics;
    const template = getState().ilab.metricTemplate;

    let graphs = [];
    uids.forEach(async (uid) => {
      const run = getState().ilab.results.find((i) => i.id === uid);
      const periods = filterPeriods.find((i) => i.uid == uid);
      periods?.periods?.forEach((p) => {
        if (p.is_primary) {
          graphs.push({
            run: uid,
            metric: p.primary_metric,
            aggregate: true,
            periods: [p.id],
            title: makeTitle(run, p, p.primary_metric, template),
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
                title: makeTitle(run, p, metric, template),
              });
            }
          });
        }
      });
    });
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

/**
 * Fetch and store a page of results if not already in the store.
 *
 * @param {number} newPage
 */
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

/**
 * Updated the selected metric list
 * was previously present.
 *
 * @param {string} metric
 */
export const setSelectedMetrics = (metrics) => ({
  type: TYPES.SET_ILAB_SELECTED_METRICS,
  payload: metrics,
});

/**
 * Help to manage the set of accordion folds that are open.
 */
export const getMetaRowdId = () => (dispatch, getState) => {
  const results = getState().ilab.results;
  const metaId = results.map((item) => `metadata-toggle-${item.id}`);
  dispatch(setMetaRowExpanded(metaId));
};

/**
 * Toggle the state of the comparison view.
 */
export const toggleComparisonSwitch = () => ({
  type: TYPES.TOGGLE_COMPARISON_SWITCH,
});

/**
 * Store the set of expanded rows.
 *
 * @param {Array[string]} expandedItems list of currently expanded runs
 */
export const setMetaRowExpanded = (expandedItems) => ({
  type: TYPES.SET_EXPANDED_METAROW,
  payload: expandedItems,
});

export const updateURL = (navigate) => (dispatch, getState) => {
  const { perPage, offset, page, comparisonSwitch, start_date, end_date } =
    getState().ilab;

  appendQueryString(
    {
      size: perPage,
      offset,
      page,
      comparisonSwitch,
      ...(start_date ? { start_date } : {}),
      ...(end_date ? { end_date } : {}),
    },
    navigate
  );
};

export const updateFromURL = (searchParams) => (dispatch, getState) => {
  const { perPage, offset, page, comparisonSwitch } = getState().ilab;
  if (
    "comparisonSwitch" in searchParams &&
    String(comparisonSwitch) !== searchParams["comparisonSwitch"][0]
  ) {
    dispatch(toggleComparisonSwitch());
  }
  if (
    "offset" in searchParams &&
    String(offset) !== searchParams["offset"][0]
  ) {
    dispatch({
      type: TYPES.SET_ILAB_OFFSET,
      payload: searchParams["offset"][0],
    });
  }
  if ("page" in searchParams) {
    if (String(page) !== searchParams["page"][0]) {
      dispatch(setIlabPage(searchParams["page"][0]));
    }
    if ("size" in searchParams && String(perPage) !== searchParams["size"][0]) {
      dispatch(
        setIlabPageOptions(searchParams["page"][0], searchParams["size"][0])
      );
    }
  }
};

export const retrieveGraphAndSummary = (ids) => async (dispatch) => {
  if (ids.length === 1) {
    await Promise.all([
      dispatch(fetchGraphData(ids[0])),
      dispatch(fetchSummaryData(ids[0])),
    ]);
  } else {
    await Promise.all([
      dispatch(fetchMultiGraphData(ids)),
      dispatch(handleSummaryData(ids)),
    ]);
  }
};

export const fetchRowAPIs = (run) => async (dispatch) => {
  await Promise.all([
    dispatch(fetchPeriods(run.id)),
    dispatch(fetchMetricsInfo(run.id)),
    dispatch(fetchGraphData(run.id)),
    dispatch(fetchSummaryData(run.id)),
  ]);
};

export const setSelectedMetricsPerRun =
  (id, metrics) => (dispatch, getState) => {
    const selectedMetricsPerRun = cloneDeep(
      getState().ilab.selectedMetricsPerRun
    );
    selectedMetricsPerRun[id] = metrics;

    dispatch({
      type: TYPES.SET_SELECTED_METRICS_PER_RUN,
      payload: selectedMetricsPerRun,
    });
  };
/**
 * Return the selected metrics based on the comparison switch
 *
 * @param {string} uid
 */
export const getSelectedMetrics = (uid) => (dispatch, getState) => {
  const comparisonSwitch = getState().ilab.comparisonSwitch;
  let metrics = [];
  if (comparisonSwitch) {
    metrics = getState().ilab.metrics_selected;
  } else {
    metrics = getState().ilab.selectedMetricsPerRun[uid];
  }
  return metrics;
};

export const setModalOpen = (id) => (dispatch, getState) => {
  const results = getState().ilab.results;
  let item = [];
  if (id) {
    item = results.filter((item) => item.id === id);
  }

  const isModalOpen = getState().ilab.isModalOpen;
  dispatch({
    type: TYPES.SET_MODAL_OPEN,
    payload: !isModalOpen,
  });
  dispatch({
    type: TYPES.SET_MODAL_METADATA_ITEM,
    payload: item?.[0],
  });
};
