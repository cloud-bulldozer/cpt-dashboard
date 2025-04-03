import { SET_LAST_UPDATED_TIME } from "./types";

export const setLastUpdatedTime = () => ({
  type: SET_LAST_UPDATED_TIME,
  payload: new Date().toLocaleString().replace(", ", " ").toString(),
});
