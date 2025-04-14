import {
  applyCPTDateFilter,
  removeCPTAppliedFilters,
  setCPTAppliedFilters,
  setCPTCatFilters,
  setCPTOtherSummaryFilter,
} from "./homeActions";
import {
  applyOCPDateFilter,
  removeOCPAppliedFilters,
  setOCPAppliedFilters,
  setOCPCatFilters,
  setOCPOtherSummaryFilter,
} from "./ocpActions";
import {
  removeOLSAppliedFilters,
  setOLSAppliedFilters,
  setOLSCatFilters,
  applyOLSDateFilter,
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
  } else if (currType === "ols") {
    dispatch(setOLSCatFilters(category));
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
  } else if (currType === "ols") {
    dispatch(setOLSAppliedFilters(navigation));
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
  } else if (currType === "ols") {
    dispatch(removeOLSAppliedFilters(key, value, navigation));
  }
};

export const setDateFilter = (date, key, navigation, currType) => {
  if (currType === "cpt") {
    dispatch(applyCPTDateFilter(date, key, navigation));
  } else if (currType === "ocp") {
    dispatch(applyOCPDateFilter(date, key, navigation));
  } else if (currType === "quay") {
    dispatch(applyQuayDateFilter(date, key, navigation));
  } else if (currType === "telco") {
    dispatch(applyTelcoDateFilter(date, key, navigation));
  } else if (currType === "ols") {
      dispatch(applyOLSDateFilter(date, key, navigation));
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
  } else if (currType === "ols") {
    dispatch(setOLSOtherSummaryFilter());
  }
};
