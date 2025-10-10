import * as TYPES from "@/actions/types";

const initialState = {
  kpiData: null,
  isLoading: false,
  startDate: null,
  endDate: null,
};

const kpiReducer = (state = initialState, action) => {
  switch (action.type) {
    case TYPES.SET_OCP_KPI_LOADING:
      return {
        ...state,
        isLoading: true,
      };
    case TYPES.SET_OCP_KPI_DATA:
      return {
        ...state,
        kpiData: action.payload,
      };
    case TYPES.SET_OCP_KPI_DATE_FILTER:
      return {
        ...state,
        startDate: action.payload.startDate,
        endDate: action.payload.endDate,
      };
    case TYPES.SET_OCP_KPI_COMPLETED:
      return {
        ...state,
        isLoading: false,
      };
    default:
      return state;
  }
};

export default kpiReducer;
