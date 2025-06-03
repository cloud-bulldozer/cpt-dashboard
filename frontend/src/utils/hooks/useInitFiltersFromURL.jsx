import {
  applyCPTDateFilter,
  setCPTFilterFromURL,
  setSelectedCPTFilterFromUrl,
} from "@/actions/homeActions";
import {
  applyIlabDateFilter,
  updateFromURL,
  updateURL,
} from "@/actions/ilabActions";
import {
  applyOCPDateFilter,
  setOCPFilterFromURL,
  setSelectedOCPFilterFromUrl,
} from "@/actions/ocpActions";
import {
  applyOLSDateFilter,
  setOLSFilterFromURL,
  setSelectedOLSFilterFromUrl,
} from "@/actions/olsActions";
import {
  applyQuayDateFilter,
  setFilterQuayFromURL,
  setSelectedQuayFilterFromUrl,
} from "@/actions/quayActions";
import {
  applyTelcoDateFilter,
  setSelectedTelcoFilterFromUrl,
  setTelcoFilterFromURL,
} from "@/actions/telcoActions";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useDispatch } from "react-redux";
import { useEffect } from "react";

export const useInitFiltersFromURL = (currType) => {
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const filterActionMap = {
    cpt: setCPTFilterFromURL,
    ocp: setOCPFilterFromURL,
    quay: setFilterQuayFromURL,
    telco: setTelcoFilterFromURL,
    ols: setOLSFilterFromURL,
    ilab: updateFromURL,
  };

  const selectedFilterActionMap = {
    cpt: setSelectedCPTFilterFromUrl,
    ocp: setSelectedOCPFilterFromUrl,
    quay: setSelectedQuayFilterFromUrl,
    telco: setSelectedTelcoFilterFromUrl,
    ols: setSelectedOLSFilterFromUrl,
  };

  const dateFilterMap = {
    cpt: applyCPTDateFilter,
    ocp: applyOCPDateFilter,
    quay: applyQuayDateFilter,
    telco: applyTelcoDateFilter,
    ols: applyOLSDateFilter,
    ilab: applyIlabDateFilter,
  };
  useEffect(() => {
    if (searchParams.size > 0) {
      const startDate = searchParams.get("start_date");
      const endDate = searchParams.get("end_date");

      const tempParams = new URLSearchParams(searchParams.toString());
      tempParams.delete("start_date");
      tempParams.delete("end_date");

      const filteredParams = Object.fromEntries(tempParams.entries());

      const parsedFilters = {};
      for (const key in filteredParams) {
        parsedFilters[key] = filteredParams[key].split(",");
      }

      const filterAction = filterActionMap[currType];
      if (filterAction) {
        dispatch(filterAction(parsedFilters));
      }

      if (currType !== "ilab") {
        const selectedFilterAction = selectedFilterActionMap[currType];
        if (selectedFilterAction) {
          dispatch(selectedFilterAction(filteredParams));
        }
      }
      const dateFilterAction = dateFilterMap[currType];
      if (dateFilterAction) {
        dispatch(dateFilterAction(startDate, endDate, navigate));
      }
    } else {
      if (currType === "ilab") {
        dispatch(updateURL(navigate));
      }
    }

    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};
