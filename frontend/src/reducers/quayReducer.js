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
    { name: "CI System", value: "ciSystem" },
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Platform", value: "platform" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Platform", value: "platform" },
    { name: "Worker Count", value: "workerNodesCount" },
    { name: "Status", value: "jobStatus" },
    { name: "Concurrency", value: "concurrency" },
    { name: "Hit Size", value: "hitSize" },
    { name: "Image Push/Pulls", value: "imagePushPulls" },
    { name: "Build", value: "build" },
  ],
  selectedFilters: [
    { name: "benchmark", value: [] },
    { name: "releaseStream", value: [] },
    { name: "platform", value: [] },
    { name: "workerNodesCount", value: [] },
    { name: "concurrency", value: [] },
    { name: "hitSize", value: [] },
    { name: "imagePushPulls", value: [] },
    { name: "build", value: [] },
    { name: "ciSystem", value: [] },
  ],
  clusterMetaData: [
    { name: "Release Binary", value: "releaseStream" },
    { name: "Cluster Name", value: "clusterName" },
    { name: "Cluster Type", value: "clusterType" },
    { name: "Network Type", value: "networkType" },
    { name: "Benchmark Status", value: "jobStatus" },
    { name: "Duration", value: "jobDuration" },
    { name: "Test ID", value: "uuid" },
  ],
  nodeKeys: [
    { name: "Master", value: "masterNodesType" },
    { name: "Worker", value: "workerNodesType" },
    { name: "Infra", value: "infraNodesType" },
    { name: "Workload", value: "benchmark" },
  ],
  nodeCount: [
    { name: "Master", value: "masterNodesCount" },
    { name: "Worker", value: "workerNodesCount" },
    { name: "Infra", value: "infraNodesCount" },
    { name: "Total", value: "totalNodesCount" },
  ],
  filterData: [],
  filteredResults: [],
  filterOptions: [],
  categoryFilterValue: "Benchmark",
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

const QuayReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;

  switch (type) {
    case TYPES.SET_QUAY_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_QUAY_PAGE_TOTAL:
      return {
        ...state,
        totalJobs: payload.total,
        offset: payload.offset,
      };
    case TYPES.SET_QUAY_OFFSET:
      return { ...state, offset: payload };
    case TYPES.SET_QUAY_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_QUAY_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_QUAY_SORT_DIR:
      return { ...state, activeSortDir: payload };
    case TYPES.SET_QUAY_SORT_OBJ:
      return { ...state, sort: payload };
    case TYPES.SET_QUAY_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_QUAY_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_QUAY_FILTERED_DATA:
      return { ...state, filteredResults: payload };
    case TYPES.SET_QUAY_FILTER_OPTIONS:
      return { ...state, filterOptions: payload };
    case TYPES.SET_QUAY_CATEGORY_FILTER:
      return { ...state, categoryFilterValue: payload };
    case TYPES.SET_QUAY_FILTER_DATA:
      return { ...state, filterData: payload };
    case TYPES.SET_QUAY_APPLIED_FILTERS:
      return { ...state, appliedFilters: payload };
    case TYPES.SET_QUAY_SELECTED_FILTERS:
      return { ...state, selectedFilters: payload };
    case TYPES.SET_QUAY_SUMMARY:
      return { ...state, summary: payload };
    case TYPES.SET_QUAY_COLUMNS:
      return { ...state, tableColumns: payload };
    case TYPES.SET_QUAY_GRAPH_DATA:
      return { ...state, graphData: [...state.graphData, payload] };
    default:
      return state;
  }
};

export default QuayReducer;
