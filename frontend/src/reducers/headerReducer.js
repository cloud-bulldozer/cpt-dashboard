import { SET_LAST_UPDATED_TIME } from "../actions/types";

const initialState = {
  updatedTime: "",
};
const HeaderReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case SET_LAST_UPDATED_TIME:
      return {
        ...state,
        updatedTime: payload,
      };

    default:
      return state;
  }
};

export default HeaderReducer;
