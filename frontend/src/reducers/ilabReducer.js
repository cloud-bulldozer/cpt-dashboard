import * as TYPES from "@/actions/types";

const initialState = {
  results: [],
  start_date: "",
  end_date: "",
  graphData: [],
  multiGraphData: [],
  totalItems: 0,
  page: 1,
  perPage: 10,
  size: 10,
  offset: 0,
  metrics: [],
  periods: [],
  metrics_selected: {},
  tableData: [],
  comparisonSwitch: false,
  metaRowExpanded: [],
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
      return { ...state, tableData: payload };
    case TYPES.SET_ILAB_MULTIGRAPH_DATA:
      return { ...state, multiGraphData: payload };
    case TYPES.TOGGLE_COMPARISON_SWITCH:
      return { ...state, comparisonSwitch: !state.comparisonSwitch };
    case TYPES.SET_EXPANDED_METAROW:
      return { ...state, metaRowExpanded: payload };
    default:
      return state;
  }
};

export default ILabReducer;
