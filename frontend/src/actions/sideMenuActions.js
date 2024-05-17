import * as TYPES from "./types";

export const setActiveItem = (item) => {
  return {
    type: TYPES.SET_ACTIVE_MENU_ITEM,
    payload: item,
  };
};

export const toggleSideMenu = (isOpen) => ({
  type: TYPES.TOGGLE_SIDE_MENU,
  payload: isOpen,
});
