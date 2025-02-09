import {
  setCPTPage,
  setCPTPageOptions,
  sliceCPTTableRows,
} from "./homeActions";
import { setOCPPage, setOCPPageOptions, sliceOCPTableRows } from "./ocpActions";
import { setQuayPage, setQuayPageOptions } from "./quayActions";
import { setOLSPage, setOLSPageOptions } from "./olsActions";
import { setTelcoPage, setTelcoPageOptions } from "./telcoActions";
export const setPage = (newPage, currType) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(setCPTPage(newPage));
  } else if (currType === "ocp") {
    dispatch(setOCPPage(newPage));
  } else if (currType === "quay") {
    dispatch(setQuayPage(newPage));
  } else if (currType === "telco") {
    dispatch(setTelcoPage(newPage));
  } else if (currType === "ols") {
    dispatch(setOLSPage(newPage));
  }
};

export const setPageOptions = (newPage, newPerPage, currType) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(setCPTPageOptions(newPage, newPerPage));
  } else if (currType === "ocp") {
    dispatch(setOCPPageOptions(newPage, newPerPage));
  } else if (currType === "quay") {
    dispatch(setQuayPageOptions(newPage, newPerPage));
  } else if (currType === "telco") {
    dispatch(setTelcoPageOptions(newPage, newPerPage));
  } else if (currType === "ols") {
    dispatch(setOLSPageOptions(newPage, newPerPage));
  }
};

export const sliceTableRows = (startIdx, endIdx, currType) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(sliceCPTTableRows(startIdx, endIdx));
  } else if (currType === "ocp") {
    dispatch(sliceOCPTableRows(startIdx, endIdx));
  }
};
