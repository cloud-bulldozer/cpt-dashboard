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
    { name: "Job Type", value: "jobType" },
    { name: "Build", value: "buildUrl" },
    { name: "Worker Count", value: "workerNodesCount" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "CI System", value: "ciSystem" },
    { name: "Benchmark", value: "benchmark" },
    { name: "Worker Count", value: "workerNodesCount" },
    { name: "Network Type", value: "networkType" },
    { name: "Versions", value: "ocpVersion" },
    { name: "Job Type", value: "jobType" },
    { name: "Status", value: "jobStatus" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Build", value: "build" },
  ],
  filterOptions: [],
  filterData: [],
  categoryFilterValue: "",
  activeSortDir: null,
  activeSortIndex: null,
  sort: "",
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
  offset: INITAL_OFFSET,
  totalJobs: 0,
  appliedFilters: {},
  summary: {},
  selectedFilters: [
    { name: "ciSystem", value: [] },
    { name: "benchmark", value: [] },
    { name: "workerNodesCount", value: [] },
    { name: "networkType", value: [] },
    { name: "ocpVersion", value: [] },
    { name: "jobType", value: [] },
    { name: "jobStatus", value: [] },
    { name: "startDate", value: [] },
    { name: "endDate", value: [] },
    { name: "build", value: [] },
  ],
  clusterMetaData: [
    { name: "Organization", value: "organization" },
    { name: "Cluster Name", value: "clusterName" },
    { name: "Network Type", value: "networkType" },
    { name: "Benchmark Status", value: "jobStatus" },
    { name: "Job Duration", value: "jobDuration" },
    { name: "Job Type", value: "jobType" },
    { name: "Repository", value: "repository" },
    { name: "OpenStack Compute Nodes", value: "openstackComputeNodes" },
    { name: "OpenStack Version", value: "openstackVersion" },
    { name: "Pull Number", value: "pullNumber" },
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
    { name: "Total", value: "totalNodesCount" },
  ],
};
const OSOReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case TYPES.SET_OSO_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_OSO_PAGE_TOTAL:
      return {
        ...state,
        totalJobs: payload.total,
        offset: payload.offset,
      };
    case TYPES.SET_OSO_OFFSET:
      return { ...state, offset: payload };
    case TYPES.SET_OSO_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_OSO_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_OSO_SORT_DIR:
      return { ...state, activeSortDir: payload };
    case TYPES.SET_OSO_SORT_OBJ:
      return { ...state, sort: payload };
    case TYPES.SET_OSO_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_OSO_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_OSO_SUMMARY:
      return { ...state, summary: payload };
    case TYPES.SET_OSO_FILTER_DATA:
      return { ...state, filterData: payload };
    case TYPES.SET_OSO_CATEGORY_FILTER:
      return { ...state, categoryFilterValue: payload };
    case TYPES.SET_OSO_FILTER_OPTIONS:
      return { ...state, filterOptions: payload };
    case TYPES.SET_OSO_APPLIED_FILTERS:
      return { ...state, appliedFilters: payload };
    case TYPES.SET_SELECTED_OSO_FILTERS:
      return { ...state, selectedFilters: payload };
    case TYPES.SET_OSO_COLUMNS:
      return { ...state, tableColumns: payload };
    default:
      return state;
  }
};
export default OSOReducer;
