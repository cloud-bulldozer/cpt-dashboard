import { setCPTSortDir, setCPTSortIndex } from "./homeActions";
import { setOCPSortDir, setOCPSortIndex } from "./ocpActions";
import { setOLSSortDir, setOLSSortIndex } from "./olsActions";
import { setQuaySortDir, setQuaySortIndex } from "./quayActions";
import { setTelcoSortDir, setTelcoSortIndex } from "./telcoActions";

import { sortTable } from "./commonActions";
import store from "@/store/store";

const { dispatch } = store;
export const setActiveSortDir = (dir, currType) => {
  if (currType === "cpt") {
    dispatch(setCPTSortDir(dir));
  } else if (currType === "ocp") {
    dispatch(setOCPSortDir(dir));
  } else if (currType === "quay") {
    dispatch(setQuaySortDir(dir));
  } else if (currType === "telco") {
    dispatch(setTelcoSortDir(dir));
  } else if (currType === "ols") {
    dispatch(setOLSSortDir(dir));
  }
};
export const setActiveSortIndex = (index, currType) => {
  if (currType === "cpt") {
    dispatch(setCPTSortIndex(index));
  } else if (currType === "ocp") {
    dispatch(setOCPSortIndex(index));
  } else if (currType === "quay") {
    dispatch(setQuaySortIndex(index));
  } else if (currType === "telco") {
    dispatch(setTelcoSortIndex(index));
  } else if (currType === "ols") {
    dispatch(setOLSSortIndex(index));
  }
};
export const handleOnSort = (currType) => {
  dispatch(sortTable(currType));
};
