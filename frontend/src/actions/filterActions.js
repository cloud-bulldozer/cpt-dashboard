import { fetchILabJobs, setIlabDateFilter } from "./ilabActions";
import {
  removeCPTAppliedFilters,
  setCPTAppliedFilters,
  setCPTCatFilters,
  setCPTDateFilter,
  setCPTOtherSummaryFilter,
} from "./homeActions";
import {
  removeOCPAppliedFilters,
  setOCPAppliedFilters,
  setOCPCatFilters,
  setOCPDateFilter,
  setOCPOtherSummaryFilter,
} from "./ocpActions";
import {
  removeQuayAppliedFilters,
  setQuayAppliedFilters,
  setQuayCatFilters,
  setQuayDateFilter,
  setQuayOtherSummaryFilter,
} from "./quayActions";
import {
  removeTelcoAppliedFilters,
  setTelcoAppliedFilters,
  setTelcoCatFilters,
  setTelcoDateFilter,
  setTelcoOtherSummaryFilter,
} from "./telcoActions";

import store from "@/store/store";

const { dispatch } = store;

export const setCatFilters = (category, currType) => {
  if (currType === "cpt") {
    dispatch(setCPTCatFilters(category));
  } else if (currType === "ocp") {
    dispatch(setOCPCatFilters(category));
  } else if (currType === "quay") {
    dispatch(setQuayCatFilters(category));
  } else if (currType === "telco") {
    dispatch(setTelcoCatFilters(category));
  }
};

export const setAppliedFilters = (navigation, currType) => {
  if (currType === "cpt") {
    dispatch(setCPTAppliedFilters(navigation));
  } else if (currType === "ocp") {
    dispatch(setOCPAppliedFilters(navigation));
  } else if (currType === "quay") {
    dispatch(setQuayAppliedFilters(navigation));
  } else if (currType === "telco") {
    dispatch(setTelcoAppliedFilters(navigation));
  }
};

export const removeAppliedFilters = (key, value, navigation, currType) => {
  if (currType === "cpt") {
    dispatch(removeCPTAppliedFilters(key, value, navigation));
  } else if (currType === "ocp") {
    dispatch(removeOCPAppliedFilters(key, value, navigation));
  } else if (currType === "quay") {
    dispatch(removeQuayAppliedFilters(key, value, navigation));
  } else if (currType === "telco") {
    dispatch(removeTelcoAppliedFilters(key, value, navigation));
  }
};

export const setDateFilter = (date, key, navigation, currType) => {
  if (currType === "cpt") {
    dispatch(setCPTDateFilter(date, key, navigation));
  } else if (currType === "ocp") {
    dispatch(setOCPDateFilter(date, key, navigation));
  } else if (currType === "quay") {
    dispatch(setQuayDateFilter(date, key, navigation));
  } else if (currType === "telco") {
    dispatch(setTelcoDateFilter(date, key, navigation));
  } else if (currType === "ilab") {
    dispatch(setIlabDateFilter(date, key, navigation));
    dispatch(fetchILabJobs());
  }
};

export const setOtherSummaryFilter = (currType) => {
  if (currType === "cpt") {
    dispatch(setCPTOtherSummaryFilter());
  } else if (currType === "ocp") {
    dispatch(setOCPOtherSummaryFilter());
  } else if (currType === "quay") {
    dispatch(setQuayOtherSummaryFilter());
  } else if (currType === "telco") {
    dispatch(setTelcoOtherSummaryFilter());
  }
};
