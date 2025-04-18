import { SET_LAST_UPDATED_TIME, SET_AGGREGATOR_VERSION } from "../actions/types";

const initialState = {
  updatedTime: "",
  aggregatorVersion: {version: "unknown"},
};
const HeaderReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case SET_LAST_UPDATED_TIME:
      return {
        ...state,
        updatedTime: payload,
      };
    case SET_AGGREGATOR_VERSION:
      return {
        ...state,
        aggregatorVersion: payload,
      }
    default:
      return state;
  }
};

export default HeaderReducer;
