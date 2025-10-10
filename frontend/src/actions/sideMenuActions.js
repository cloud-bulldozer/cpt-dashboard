import * as TYPES from "./types";

import { appendQueryString } from "@/utils/helper.js";

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

export const setFromSideMenuFlag = (fromSideMenu) => ({
  type: TYPES.SET_FROM_SIDE_MENU_FLAG,
  payload: fromSideMenu,
});

export const maintainQueryString =
  (toPage, type, navigate) => (dispatch, getState) => {
    // KPI tab doesn't have filters, so just navigate directly
    if (type === "kpi") {
      navigate({
        pathname: toPage,
      });
      return;
    }
    
    const { appliedFilters, start_date, end_date } = getState()[type];
    appendQueryString(
      { ...appliedFilters, start_date, end_date },
      navigate,
      toPage
    );
  };
