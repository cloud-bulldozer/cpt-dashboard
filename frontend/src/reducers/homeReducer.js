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
  tableData: [],
  tableColumns: [
    { name: "Product", value: "product" },
    { name: "CI System", value: "ciSystem" },
    { name: "Test Name", value: "testName" },
    { name: "Version", value: "version" },
    { name: "Release Stream", value: "releaseStream" },
    { name: "Build URL", value: "buildUrl" },
    { name: "Start Date", value: "startDate" },
    { name: "End Date", value: "endDate" },
    { name: "Status", value: "jobStatus" },
  ],
  tableFilters: [
    { name: "Product", value: "product" },
    { name: "CI System", value: "ciSystem" },
    { name: "Test Name", value: "testName" },
    { name: "Status", value: "jobStatus" },
    { name: "Release Stream", value: "releaseStream" },
  ],
  filterData: [],
  activeSortDir: null,
  activeSortIndex: null,
  sort: "",
  categoryFilterValue: "",
  filterOptions: [],
  appliedFilters: {},
  selectedFilters: [
    { name: "releaseStream", value: [] },
    { name: "product", value: [] },
    { name: "ciSystem", value: [] },
    { name: "testName", value: [] },
    { name: "jobStatus", value: [] },
  ],
  filteredResults: [],
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
  offset: INITAL_OFFSET,
  totalJobs: 0,
  summary: {},
};

const HomeReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case TYPES.SET_CPT_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_CPT_PAGE_TOTAL:
      return {
        ...state,
        totalJobs: payload.total,
        offset: payload.offset,
      };
    case TYPES.SET_CPT_OFFSET:
      return { ...state, offset: payload };
    case TYPES.SET_CPT_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_CPT_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_CPT_SORT_DIR:
      return { ...state, activeSortDir: payload };
    case TYPES.SET_CPT_FILTER_DATA:
      return { ...state, filterData: payload };
    case TYPES.SET_CATEGORY_FILTER:
      return { ...state, categoryFilterValue: payload };
    case TYPES.SET_FILTER_OPTIONS:
      return { ...state, filterOptions: payload };
    case TYPES.SET_APPLIED_FILTERS:
      return { ...state, appliedFilters: payload };
    case TYPES.SET_FILTERED_DATA:
      return { ...state, filteredResults: payload };
    case TYPES.SET_PAGE:
      return { ...state, page: payload };
    case TYPES.SET_PAGE_OPTIONS:
      return { ...state, page: payload.page, perPage: payload.perPage };
    case TYPES.SET_CPT_SUMMARY:
      return { ...state, summary: payload };
    case TYPES.SET_SELECTED_FILTERS:
      return { ...state, selectedFilters: payload };
    default:
      return state;
  }
};

export default HomeReducer;
