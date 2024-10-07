import * as TYPES from "./types";

import { uid } from "@/utils/helper";

export const showFailureToast = () => async (dispatch) => {
  const toast = {
    variant: "danger",
    title: "Something went wrong",
    message: "Please try again later",
  };
  dispatch(showToast(toast.variant, toast.title, toast.message));
};

export const showToast =
  (variant, title, message = "") =>
  (dispatch, getState) => {
    const obj = {
      variant: variant,
      title: title,
      message: message,
      key: uid(),
    };
    const alerts = [...getState().toast.alerts, obj];

    dispatch({
      type: TYPES.SHOW_TOAST,
      payload: alerts,
    });
  };

export const hideToast = (key) => (dispatch, getState) => {
  const alerts = getState().toast.alerts;
  const activeAlert = alerts.filter((item) => item.key !== key);

  dispatch({
    type: TYPES.SHOW_TOAST,
    payload: activeAlert,
  });
};

export const clearToast = () => (dispatch) => {
  dispatch({ type: TYPES.CLEAR_TOAST });
};
