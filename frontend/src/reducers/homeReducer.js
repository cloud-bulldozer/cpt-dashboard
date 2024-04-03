import * as TYPES from "@/actions/types";

const initialState = {
  results: [],
  start_date: "",
  end_date: "",
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
  activeSortDir: null,
  activeSortIndex: null,
};

const HomeReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case TYPES.SET_CPT_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_CPT_DATE_FILTER:
      return {
        ...state,
        start_date: payload.startDate,
        end_date: payload.endDate,
      };
    case TYPES.SET_CPT_SORT_INDEX:
      return { ...state, activeSortIndex: payload };
    case TYPES.SET_CPT_SORT_DIR:
      return { ...state, activeSortDir: payload };
    default:
      return state;
  }
};

export default HomeReducer;
