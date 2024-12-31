import {
  checkIlabJobs,
  setIlabPage,
  setIlabPageOptions,
  sliceIlabTableRows,
  updateURL,
} from "./ilabActions";
import {
  setCPTPage,
  setCPTPageOptions,
  sliceCPTTableRows,
} from "./homeActions";
import { setOCPPage, setOCPPageOptions, sliceOCPTableRows } from "./ocpActions";
import { setQuayPage, setQuayPageOptions } from "./quayActions";
import { setTelcoPage, setTelcoPageOptions } from "./telcoActions";

export const setPage = (newPage, currType, navigate) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(setCPTPage(newPage));
  } else if (currType === "ocp") {
    dispatch(setOCPPage(newPage));
  } else if (currType === "quay") {
    dispatch(setQuayPage(newPage));
  } else if (currType === "telco") {
    dispatch(setTelcoPage(newPage));
  } else if (currType === "ilab") {
    dispatch(setIlabPage(newPage));
    dispatch(updateURL(navigate));
  }
};

export const setPageOptions =
  (newPage, newPerPage, currType, navigate) => (dispatch) => {
    if (currType === "cpt") {
      dispatch(setCPTPageOptions(newPage, newPerPage));
    } else if (currType === "ocp") {
      dispatch(setOCPPageOptions(newPage, newPerPage));
    } else if (currType === "quay") {
      dispatch(setQuayPageOptions(newPage, newPerPage));
    } else if (currType === "telco") {
      dispatch(setTelcoPageOptions(newPage, newPerPage));
    } else if (currType === "ilab") {
      dispatch(setIlabPageOptions(newPage, newPerPage));
      dispatch(updateURL(navigate));
    }
  };

export const sliceTableRows = (startIdx, endIdx, currType) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(sliceCPTTableRows(startIdx, endIdx));
  } else if (currType === "ocp") {
    dispatch(sliceOCPTableRows(startIdx, endIdx));
  } else if (currType === "ilab") {
    dispatch(sliceIlabTableRows(startIdx, endIdx));
  }
};

export const fetchNextJobs = (newPage) => (dispatch) => {
  dispatch(checkIlabJobs(newPage));
};
