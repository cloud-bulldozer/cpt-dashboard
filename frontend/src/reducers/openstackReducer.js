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
  activeSortDir: null,
  activeSortIndex: null,
  sort: "",
  page: START_PAGE,
  perPage: DEFAULT_PER_PAGE,
  offset: INITAL_OFFSET,
  totalJobs: 0,
  appliedFilters: {},
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
    default:
      return state;
  }
};
export default OSOReducer;
