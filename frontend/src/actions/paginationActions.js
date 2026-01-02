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
  sliceCPTTableRows,
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
import {
  fetchOLSJobsData,
  setOLSOffset,
  setOLSPage,
  setOLSPageOptions,
} from "./olsActions";
import {
  fetchIlabJobs,
  setIlabOffset,
  setIlabPage,
  setIlabPageOptions,
} from "./ilabActions";

import {
  setOSOPage,
  setOSOPageOptions,
  fetchOSOJobs,
  setOSOoffset,
} from "./openstackActions";

export const setPage = (newPage, currType) => (dispatch) => {
  const actions = {
    cpt: setCPTPage,
    ocp: setOCPPage,
    quay: setQuayPage,
    telco: setTelcoPage,
    ols: setOLSPage,
    ilab: setIlabPage,
    oso: setOSOPage,
  };
  dispatch(actions[currType](newPage));
};

export const setPageOptions = (newPage, newPerPage, currType) => (dispatch) => {
  const actions = {
    cpt: setCPTPageOptions,
    ocp: setOCPPageOptions,
    quay: setQuayPageOptions,
    telco: setTelcoPageOptions,
    ols: setOLSPageOptions,
    ilab: setIlabPageOptions,
    oso: setOSOPageOptions,
  };
  dispatch(actions[currType](newPage, newPerPage));
};

const calculateOffset = (pageNumber, itemsPerPage) => {
  return (pageNumber - 1) * itemsPerPage;
};

const fetchActions = {
  ocp: fetchOCPJobs,
  quay: fetchQuayJobsData,
  telco: fetchTelcoJobsData,
  cpt: fetchOCPJobsData,
  ols: fetchOLSJobsData,
  ilab: fetchIlabJobs,
  oso: fetchOSOJobs,
};
const offsetActions = {
  ocp: setOCPOffset,
  quay: setQuayOffset,
  telco: setTelcoOffset,
  cpt: setCPTOffset,
  ols: setOLSOffset,
  ilab: setIlabOffset,
  oso: setOSOoffset,
};

export const checkTableData = (newPage, currType) => (dispatch, getState) => {
  const { results, totalJobs, perPage, page } = getState()[currType];

  const hasPageData = results.length >= newPage * perPage;
  const offset = calculateOffset(newPage, perPage);

  if (currType === "cpt") {
    const startIdx = (page - 1) * perPage;
    const endIdx = startIdx + perPage - 1;
    if (results.length < totalJobs && !hasPageData) {
      if (results[startIdx] === undefined || results[endIdx] === undefined) {
        dispatch(fetchOCPJobsData());
      }
    } else {
      dispatch(sliceCPTTableRows(startIdx, endIdx));
    }
  } else if (results.length < totalJobs) {
    dispatch(offsetActions[currType](offset));
    dispatch(fetchActions[currType]());
  }
};
