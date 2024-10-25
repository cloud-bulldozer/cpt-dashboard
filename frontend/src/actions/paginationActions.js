import {
  fetchOCPJobs,
  setOCPOffset,
  setOCPPage,
  setOCPPageOptions,
} from "./ocpActions";
import {
  fetchOCPJobsData,
  setCPTOffset,
  setCPTPage,
  setCPTPageOptions,
} from "./homeActions";
import {
  fetchQuayJobsData,
  setQuayOffset,
  setQuayPage,
  setQuayPageOptions,
} from "./quayActions";
import {
  fetchTelcoJobsData,
  setTelcoOffset,
  setTelcoPage,
  setTelcoPageOptions,
} from "./telcoActions";

export const setPage = (newPage, currType) => (dispatch) => {
  if (currType === "cpt") {
    dispatch(setCPTPage(newPage));
  } else if (currType === "ocp") {
    dispatch(setOCPPage(newPage));
  } else if (currType === "quay") {
    dispatch(setQuayPage(newPage));
  } else if (currType === "telco") {
    dispatch(setTelcoPage(newPage));
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
  }
};

const calculateOffset = (pageNumber, itemsPerPage) => {
  return (pageNumber - 1) * itemsPerPage;
};

export const checkTableData = (newPage, currType) => (dispatch, getState) => {
  const { results, totalJobs, perPage } = getState()[currType];
  const hasPageData = results.length >= newPage * perPage;
  const offset = calculateOffset(newPage, perPage);
  if (results.length < totalJobs && !hasPageData) {
    if (currType === "cpt") {
      dispatch(setCPTOffset(offset));
      dispatch(fetchOCPJobsData());
    } else if (currType === "ocp") {
      dispatch(setOCPOffset(offset));
      dispatch(fetchOCPJobs());
    } else if (currType === "quay") {
      dispatch(setQuayOffset(offset));
      dispatch(fetchQuayJobsData());
    } else if (currType === "telco") {
      dispatch(setTelcoOffset(offset));
      dispatch(fetchTelcoJobsData());
    }
  }
};
