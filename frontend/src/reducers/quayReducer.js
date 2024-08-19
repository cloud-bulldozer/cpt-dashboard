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
    { name: "Platform", value: "platform" },
    { name: "Worker Count", value: "workerNodesCount" },
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
  ],
  selectedFilters: [
    { name: "benchmark", value: [] },
    { name: "releaseStream", value: [] },
    { name: "platform", value: [] },
    { name: "workerNodesCount", value: [] },
    { name: "jobStatus", value: [] },
  ],
  filterData: [],
  filteredResults: [],
  filterOptions: [],
  categoryFilterValue: "Benchmark",
  appliedFilters: {},
  activeSortDir: null,
  activeSortIndex: null,
  tableData: [],
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
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
    case TYPES.SET_QUAY_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_QUAY_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_QUAY_INIT_JOBS:
      return { ...state, tableData: payload };
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
    default:
      return state;
  }
};

export default QuayReducer;
