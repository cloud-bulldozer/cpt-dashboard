import {
  COMPLETED,
  GRAPH_COMPLETED,
  GRAPH_LOADING,
  LOADING,
} from "@/actions/types";

const initialState = {
  isLoading: false,
  isGraphLoading: false,
};

const LoadingReducer = (state = initialState, action = {}) => {
  const { type } = action;
  switch (type) {
    case LOADING:
      return { ...state, isLoading: true };
    case COMPLETED:
      return { ...state, isLoading: false };
    case GRAPH_LOADING:
      return { ...state, isGraphLoading: true };
    case GRAPH_COMPLETED:
      return { ...state, isGraphLoading: false };

    default:
      return state;
  }
};

export default LoadingReducer;
