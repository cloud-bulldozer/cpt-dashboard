import * as TYPES from "@/actions/types";

import {
  DEFAULT_PER_PAGE,
  INITAL_OFFSET,
  START_PAGE,
} from "@/assets/constants/paginationConstants";

const initialState = {
  results: [],
  start_date: "",
  end_date: "",
  tableColumns: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "CPU", value: "cpu" },
    { name: "Node Name", value: "nodeName" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Build", value: "ocpVersion" },
    { name: "CPU", value: "cpu" },
    { name: "Node Name", value: "nodeName" },
    { name: "Status", value: "jobStatus" },
  ],
  selectedFilters: [
    { name: "benchmark", value: [] },
    { name: "releaseStream", value: [] },
    { name: "ocpVersion", value: [] },
    { name: "cpu", value: [] },
    { name: "nodeName", value: [] },
    { name: "jobStatus", value: [] },
  ],
  clusterMetaData: [
    { name: "Release Binary", value: "releaseStream" },
    { name: "Cluster Name", value: "nodeName" },
    { name: "Cluster Type", value: "clusterType" },
    { name: "Network Type", value: "networkType" },
    { name: "Benchmark Status", value: "jobStatus" },
    { name: "Duration", value: "jobDuration" },
  ],
  nodeKeys: [
    { name: "Master", value: "master_type" },
    { name: "Workload", value: "benchmark" },
  ],
  nodeCount: [
    { name: "Master", value: "masterNodesCount" },
    { name: "Total", value: "totalNodesCount" },
  ],
  filterData: [],
  filteredResults: [],
  categoryFilterValue: "Benchmark",
  filterOptions: [],
  appliedFilters: {},
  activeSortDir: null,
  activeSortIndex: null,
  sort: "",
  graphData: [],
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
  offset: INITAL_OFFSET,
  totalJobs: 0,
  summary: {},
};

const TelcoReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;

  switch (type) {
    case TYPES.SET_TELCO_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_TELCO_PAGE_TOTAL:
      return {
        ...state,
        totalJobs: payload.total,
        offset: payload.offset,
      };
    case TYPES.SET_TELCO_OFFSET:
      return { ...state, offset: payload };
    case TYPES.SET_TELCO_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_TELCO_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_TELCO_SORT_DIR:
      return { ...state, activeSortDir: payload };
    case TYPES.SET_TELCO_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_TELCO_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_TELCO_FILTERED_DATA:
      return { ...state, filteredResults: payload };
    case TYPES.SET_TELCO_CATEGORY_FILTER:
      return { ...state, categoryFilterValue: payload };
    case TYPES.SET_TELCO_FILTER_OPTIONS:
      return { ...state, filterOptions: payload };
    case TYPES.SET_TELCO_FILTER_DATA:
      return { ...state, filterData: payload };
    case TYPES.SET_TELCO_APPLIED_FILTERS:
      return { ...state, appliedFilters: payload };
    case TYPES.SET_TELCO_SELECTED_FILTERS:
      return { ...state, selectedFilters: payload };
    case TYPES.SET_TELCO_SUMMARY:
      return { ...state, summary: payload };
    case TYPES.SET_TELCO_COLUMNS:
      return { ...state, tableColumns: payload };
    case TYPES.SET_TELCO_GRAPH_DATA:
      return { ...state, graphData: [...state.graphData, payload] };
    default:
      return state;
  }
};

export default TelcoReducer;
