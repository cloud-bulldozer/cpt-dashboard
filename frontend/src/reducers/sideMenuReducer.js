import * as CONSTANTS from "../assets/constants/SidemenuConstants";

import {
  SET_ACTIVE_MENU_ITEM,
  SET_FROM_SIDE_MENU_FLAG,
  TOGGLE_SIDE_MENU,
} from "../actions/types";

const initialState = {
  activeMenuItem: CONSTANTS.HOME_NAV,
  isSideMenuOpen: true,
  fromSideMenu: false,
};
const SideMenuReducer = (state = initialState, action = {}) => {
  const { type, payload } = action;
  switch (type) {
    case SET_ACTIVE_MENU_ITEM:
      return {
        ...state,
        activeMenuItem: payload,
      };
    case TOGGLE_SIDE_MENU:
      return { ...state, isSideMenuOpen: payload };
    case SET_FROM_SIDE_MENU_FLAG:
      return { ...state, fromSideMenu: payload };
    default:
      return state;
  }
};

export default SideMenuReducer;
