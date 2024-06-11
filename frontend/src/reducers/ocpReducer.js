import * as TYPES from "@/actions/types";

import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";

const initialState = {
  results: [],
  start_date: "",
  end_date: "",
  tableColumns: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Build", value: "build" },
    { name: "Worker Count", value: "workerNodesCount" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "CI System", value: "ciSystem" },
    { name: "Platform", value: "platform" },
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Build", value: "build" },
    { name: "Worker Count", value: "workerNodesCount" },
    { name: "Network Type", value: "networkType" },
    { name: "Versions", value: "shortVersion" },
    { name: "Job Type", value: "jobType" },
    { name: "Rehearse", value: "isRehearse" },
    { name: "Has IPSEC", value: "ipsec" },
    { name: "FIPS Enabled", value: "fips" },
    { name: "Is Encrypted", value: "encrypted" },
    { name: "Control Plane Access", value: "publish" },
    { name: "Compute Architecture", value: "computeArch" },
    { name: "Control Plane Architecture", value: "controlPlaneArch" },
    { name: "Status", value: "jobStatus" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
  ],
  activeSortDir: null,
  activeSortIndex: null,
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
  tableData: [],
  filterData: [],
  categoryFilterValue: "",
  filterOptions: [],
  appliedFilters: {},
  filteredResults: [],
  summary: {},
  graphData: [],
  clusterMetaData: [
    { name: "Release Binary", value: "releaseStream" },
    { name: "Cluster Name", value: "clusterName" },
    { name: "Cluster Type", value: "clusterType" },
    { name: "Network Type", value: "networkType" },
    { name: "Benchmark Status", value: "jobStatus" },
    { name: "Job Duration", value: "jobDuration" },
    { name: "Job Type", value: "jobType" },
    { name: "Rehearse", value: "isRehearse" },
    { name: "Has IPSEC", value: "ipsec" },
    { name: "FIPS Enabled", value: "fips" },
    { name: "Is Encrypted", value: "encrypted" },
    { name: "Control Plane Access", value: "publish" },
    { name: "Compute Architecture", value: "computeArch" },
    { name: "Control Plane Architecture", value: "controlPlaneArch" },
  ],
  nodeKeys: [
    { name: "Master", value: "masterNodesCount" },
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
};

const OCPReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;

  switch (type) {
    case TYPES.SET_OCP_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_OCP_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_OCP_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_OCP_SORT_DIR:
      return { ...state, activeSortDir: payload };
    case TYPES.SET_OCP_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_OCP_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_OCP_INIT_JOBS:
      return { ...state, tableData: payload };
    case TYPES.SET_OCP_SUMMARY:
      return { ...state, summary: payload };
    case TYPES.SET_OCP_FILTER_DATA:
      return { ...state, filterData: payload };
    case TYPES.SET_OCP_CATEGORY_FILTER:
      return { ...state, categoryFilterValue: payload };
    case TYPES.SET_OCP_FILTER_OPTIONS:
      return { ...state, filterOptions: payload };
    case TYPES.SET_OCP_FILTERED_DATA:
      return { ...state, filteredResults: payload };
    case TYPES.SET_OCP_APPLIED_FILTERS:
      return { ...state, appliedFilters: payload };
    case TYPES.SET_OCP_GRAPH_DATA:
      return { ...state, graphData: [...state.graphData, payload] };
    case TYPES.SET_OCP_COLUMNS:
      return { ...state, tableColumns: payload };
    default:
      return state;
  }
};
export default OCPReducer;
