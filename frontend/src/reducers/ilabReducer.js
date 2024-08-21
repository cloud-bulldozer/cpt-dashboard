import * as TYPES from "@/actions/types";

const initialState = {
  results: [],
  start_date: "",
  end_date: "",
  graphData: [],
};
const ILabReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case TYPES.SET_ILAB_JOBS_DATA:
      return {
        ...state,
        results: payload,
      };
    case TYPES.SET_ILAB_DATE_FILTER:
      return {
        ...state,
        start_date: payload.start_date,
        end_date: payload.end_date,
      };
    case TYPES.SET_ILAB_GRAPH_DATA:
      return { ...state, graphData: [...state.graphData, payload] };
    default:
      return state;
  }
};

export default ILabReducer;
