import * as TYPES from "@/actions/types";

const initialState = {
  results: [],
  runFilters: {},
  metricTemplate: [],
  start_date: "",
  end_date: "",
  graphData: [],
  multiGraphData: [],
  isSummaryLoading: false,
  summaryData: [],
  totalItems: 0,
  tableColumns: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Start Date", value: "begin_date" },
    { name: "End Date", value: "end_date" },
    { name: "Status", value: "status" },
  ],
  tableFilters: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Start Date", value: "begin_date" },
    { name: "End Date", value: "end_date" },
  ],
  activeSortDir: null,
  activeSortIndex: null,
  sort: "",
  filterData: [],
  categoryFilterValue: "",
  filterOptions: [],
  appliedFilters: {},
  filteredResults: [],
  summary: {},
  page: 1,
  perPage: 10,
  size: 10,
  offset: 0,
  metrics: [],
  periods: [],
  filterOptions: [],
  metrics_selected: [],
  comparisonSwitch: false,
  metaRowExpanded: [],
  selectedMetricsPerRun: {},
};
const ILabReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case TYPES.SET_ILAB_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_ILAB_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_ILAB_TOTAL_ITEMS:
      return {
        ...state,
        totalItems: payload,
      };
    case TYPES.SET_ILAB_OFFSET:
      return { ...state, offset: payload };
    case TYPES.SET_ILAB_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_ILAB_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_ILAB_METRICS:
      return { ...state, metrics: [...state.metrics, payload] };
    case TYPES.SET_ILAB_PERIODS:
      return { ...state, periods: [...state.periods, payload] };
    case TYPES.SET_ILAB_SELECTED_METRICS:
      return {
        ...state,
        metrics_selected: payload,
      };
    case TYPES.SET_ILAB_GRAPH_DATA:
      return { ...state, graphData: payload };
    case TYPES.SET_ILAB_INIT_JOBS:
      return { ...state, results: payload };
    case TYPES.SET_ILAB_MULTIGRAPH_DATA:
      return { ...state, multiGraphData: payload };
    case TYPES.TOGGLE_COMPARISON_SWITCH:
      return { ...state, comparisonSwitch: !state.comparisonSwitch };
    case TYPES.SET_EXPANDED_METAROW:
      return { ...state, metaRowExpanded: payload };
    case TYPES.SET_ILAB_SUMMARY_LOADING:
      return { ...state, isSummaryLoading: true };
    case TYPES.SET_ILAB_SUMMARY_COMPLETE:
      return { ...state, isSummaryLoading: false };
    case TYPES.SET_ILAB_SUMMARY_DATA:
      return {
        ...state,
        summaryData: [
          ...state.summaryData.filter((i) => i.uid !== payload.uid),
          payload,
        ],
      };
    case TYPES.SET_ILAB_RUN_FILTERS:
      return { ...state, runFilters: payload };
    case TYPES.SET_ILAB_METRIC_TEMPLATE:
      return { ...state, metricTemplate: payload };
    case TYPES.SET_SELECTED_METRICS_PER_RUN:
      return { ...state, selectedMetricsPerRun: payload };
    default:
      return state;
  }
};

export default ILabReducer;
