import {
  applyCPTDateFilter,
  removeCPTAppliedFilters,
  setCPTAppliedFilters,
  setCPTCatFilters,
  setCPTOtherSummaryFilter,
} from "./homeActions";
import {
  applyIlabDateFilter,
  removeIlabAppliedFilters,
  setIlabAppliedFilters,
  setIlabCatFilters,
  setIlabOtherSummaryFilter,
} from "./ilabActions";
import {
  applyOCPDateFilter,
  removeOCPAppliedFilters,
  setOCPAppliedFilters,
  setOCPCatFilters,
  setOCPOtherSummaryFilter,
} from "./ocpActions";
import {
  applyOLSDateFilter,
  removeOLSAppliedFilters,
  setOLSAppliedFilters,
  setOLSCatFilters,
  setOLSOtherSummaryFilter,
} from "./olsActions";
import {
  applyQuayDateFilter,
  removeQuayAppliedFilters,
  setQuayAppliedFilters,
  setQuayCatFilters,
  setQuayOtherSummaryFilter,
} from "./quayActions";
import {
  applyTelcoDateFilter,
  removeTelcoAppliedFilters,
  setTelcoAppliedFilters,
  setTelcoCatFilters,
  setTelcoOtherSummaryFilter,
} from "./telcoActions";
import { fetchILabJobs, setIlabDateFilter } from "./ilabActions";

import store from "@/store/store";

const { dispatch } = store;

export const setCatFilters = (category, currType) => {
  const actions = {
    cpt: setCPTCatFilters,
    ocp: setOCPCatFilters,
    quay: setQuayCatFilters,
    telco: setTelcoCatFilters,
    ols: setOLSCatFilters,
    ilab: setIlabCatFilters,
  };
  dispatch(actions[currType](category));
};

export const setAppliedFilters = (navigation, currType) => {
  const actions = {
    cpt: setCPTAppliedFilters,
    ocp: setOCPAppliedFilters,
    quay: setQuayAppliedFilters,
    telco: setTelcoAppliedFilters,
    ols: setOLSAppliedFilters,
    ilab: setIlabAppliedFilters,
  };
  dispatch(actions[currType](navigation));
};

export const removeAppliedFilters = (key, value, navigation, currType) => {
  const actions = {
    cpt: removeCPTAppliedFilters,
    ocp: removeOCPAppliedFilters,
    quay: removeQuayAppliedFilters,
    telco: removeTelcoAppliedFilters,
    ols: removeOLSAppliedFilters,
    ilab: removeIlabAppliedFilters,
  };
  dispatch(actions[currType](key, value, navigation));
};

export const setDateFilter = (date, key, navigation, currType) => {
  const actions = {
    cpt: applyCPTDateFilter,
    ocp: applyOCPDateFilter,
    quay: applyQuayDateFilter,
    telco: applyTelcoDateFilter,
    ols: applyOLSDateFilter,
    ilab: applyIlabDateFilter,
  };
  dispatch(actions[currType](date, key, navigation));
};

export const setOtherSummaryFilter = (currType) => {
  const actions = {
    cpt: setCPTOtherSummaryFilter,
    ocp: setOCPOtherSummaryFilter,
    quay: setQuayOtherSummaryFilter,
    telco: setTelcoOtherSummaryFilter,
    ols: setOLSOtherSummaryFilter,
    ilab: setIlabOtherSummaryFilter,
  };
  dispatch(actions[currType]());
};
