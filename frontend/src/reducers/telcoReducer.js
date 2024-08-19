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
    { name: "Build", value: "TELCOVersion" },
    { name: "CPU", value: "cpu_util" },
    { name: "Node Name", value: "nodeName" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "Benchmark", value: "benchmark" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Build", value: "TELCOVersion" },
    { name: "CPU", value: "cpu_util" },
    { name: "Node Name", value: "nodeName" },
    { name: "Status", value: "jobStatus" },
  ],
  filterData: [],
  filteredResults: [],
  activeSortDir: null,
  activeSortIndex: null,
  tableData: [],
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
};

const TelcoReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;

  switch (type) {
    case TYPES.SET_TELCO_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
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
    case TYPES.SET_TELCO_INIT_JOBS:
      return { ...state, tableData: payload };
    case TYPES.SET_TELCO_FILTERED_DATA:
      return { ...state, filteredResults: payload };
    default:
      return state;
  }
};

export default TelcoReducer;
