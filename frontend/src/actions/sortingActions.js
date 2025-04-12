import * as TYPES from "@/actions/types.js";

import { fetchOCPJobs, setOCPSortDir, setOCPSortIndex } from "./ocpActions";
import { fetchOLSJobsData, setOLSSortDir, setOLSSortIndex } from "./olsActions";
import {
  fetchQuayJobsData,
  setQuaySortDir,
  setQuaySortIndex,
} from "./quayActions";
import {
  fetchTelcoJobsData,
  setTelcoSortDir,
  setTelcoSortIndex,
} from "./telcoActions";
import { setCPTSortDir, setCPTSortIndex } from "./homeActions";

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
export const handleOnSort = (colName, currType) => {
  dispatch(sortTable(colName, currType));
};

const offsetActions = {
  cpt: TYPES.SET_CPT_OFFSET,
  ocp: TYPES.SET_OCP_OFFSET,
  quay: TYPES.SET_QUAY_OFFSET,
  telco: TYPES.SET_TELCO_OFFSET,
  ols: TYPES.SET_OLS_OFFSET,
};
const fetchJobsMap = {
  ocp: fetchOCPJobs,
  quay: fetchQuayJobsData,
  telco: fetchTelcoJobsData,
  ols: fetchOLSJobsData,
};
const sortObjActions = {
  ocp: TYPES.SET_OCP_SORT_OBJ,
  quay: TYPES.SET_QUAY_SORT_OBJ,
  ols: TYPES.SET_OLS_SORT_OBJ,
};
export const sortTable = (colName, currState) => (dispatch, getState) => {
  const { activeSortDir, activeSortIndex } = getState()[currState];
  const countObj = [
    "masterNodesCount",
    "workerNodesCount",
    "infraNodesCount",
    "totalNodesCount",
    "startDate",
    "endDate",
  ];
  try {
    if (
      typeof activeSortDir !== "undefined" &&
      typeof activeSortIndex !== "undefined"
    ) {
      dispatch({ type: offsetActions[currState], payload: 0 });
      let fieldName = countObj.includes(colName)
        ? colName
        : `${colName}.keyword`;
      if (colName === "build") {
        fieldName = "ocpVersion.keyword";
      }

      const sortParam = `${fieldName}:${activeSortDir}`;
      dispatch({ type: sortObjActions[currState], payload: sortParam });
      console.log(sortParam);
      const isFromSorting = true;

      dispatch(fetchJobsMap[currState](isFromSorting));
    }
  } catch (error) {
    console.log(error);
  }
};
