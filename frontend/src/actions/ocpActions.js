import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import { appendDateFilter, appendQueryString } from "@/utils/helper.js";
import { deleteAppliedFilters, getSelectedFilter } from "./commonActions";

import API from "@/utils/axiosInstance";
import { cloneDeep } from "lodash";
import { showFailureToast } from "./toastActions";

export const fetchOCPJobs =
  (shouldStartFresh = false) =>
  async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.LOADING });
      const { results, sort } = getState().ocp;

      console.log(JSON.stringify(sort));
      const params = dispatch(getRequestParams());

      const response = await API.get(API_ROUTES.OCP_JOBS_API_V1, { params });
      if (response.status === 200) {
        const startDate = response.data.startDate,
          endDate = response.data.endDate;
        //on initial load startDate and endDate are empty, so from response append to url
        appendDateFilter(startDate, endDate);
        dispatch({
          type: TYPES.SET_OCP_DATE_FILTER,
          payload: {
            start_date: startDate,
            end_date: endDate,
          },
        });
      }
      if (response?.data?.results?.length > 0) {
        if (shouldStartFresh) {
          dispatch(setOCPPage(1));
        }
        dispatch({
          type: TYPES.SET_OCP_JOBS_DATA,
          payload: shouldStartFresh
            ? response.data.results
            : [...results, ...response.data.results],
        });

        dispatch({
          type: TYPES.SET_OCP_PAGE_TOTAL,
          payload: {
            total: response.data.total,
            offset: response.data.offset,
          },
        });
        dispatch(tableReCalcValues());
      }
    } catch (error) {
      dispatch(showFailureToast());
    }
    dispatch({ type: TYPES.COMPLETED });
  };

export const setOCPPage = (pageNo) => ({
  type: TYPES.SET_OCP_PAGE,
  payload: pageNo,
});
export const setOCPOffset = (offset) => ({
  type: TYPES.SET_OCP_OFFSET,
  payload: offset,
});

const getRequestParams = () => (dispatch, getState) => {
  const { start_date, end_date, size, offset, sort, appliedFilters } =
    getState().ocp;
  const params = {
    pretty: true,
    ...(start_date && { start_date }),
    ...(end_date && { end_date }),
    size: size,
    offset: offset,
  };
  if (Object.keys(sort).length > 0) {
    params["sort"] = JSON.stringify(sort);
  }
  if (Object.keys(appliedFilters).length > 0) {
    params["filter"] = JSON.stringify(appliedFilters);
  }
  return params;
};
export const setOCPPageOptions = (page, perPage) => ({
  type: TYPES.SET_OCP_PAGE_OPTIONS,
  payload: { page, perPage },
});

export const sliceOCPTableRows = (startIdx, endIdx) => (dispatch, getState) => {
  const results = [...getState().ocp.results];

  dispatch({
    type: TYPES.SET_OCP_INIT_JOBS,
    payload: results.slice(startIdx, endIdx),
  });
};

export const setOCPSortIndex = (index) => ({
  type: TYPES.SET_OCP_SORT_INDEX,
  payload: index,
});

export const setOCPSortDir = (direction) => ({
  type: TYPES.SET_OCP_SORT_DIR,
  payload: direction,
});

export const setOCPCatFilters = (category) => (dispatch, getState) => {
  const filterData = [...getState().ocp.filterData];
  const options = filterData.filter((item) => item.name === category)[0].value;
  const list = options.map((item) => ({
    name: item,
    value: item,
  }));

  dispatch({
    type: TYPES.SET_OCP_CATEGORY_FILTER,
    payload: category,
  });
  dispatch({
    type: TYPES.SET_OCP_FILTER_OPTIONS,
    payload: list,
  });
};

export const applyFilters = () => (dispatch) => {
  dispatch(setOCPPage(1));

  dispatch(fetchOCPJobs(true));

  dispatch(tableReCalcValues());
  dispatch(buildFilterData());
};

export const setSelectedFilterFromUrl = (params) => (dispatch, getState) => {
  const selectedFilters = cloneDeep(getState().ocp.selectedFilters);
  for (const key in params) {
    selectedFilters.find((i) => i.name === key).value = params[key].split(",");
  }
  dispatch({
    type: TYPES.SET_SELECTED_OCP_FILTERS,
    payload: selectedFilters,
  });
};
export const setSelectedFilter =
  (selectedCategory, selectedOption, isFromMetrics) => (dispatch) => {
    const selectedFilters = dispatch(
      getSelectedFilter(selectedCategory, selectedOption, "ocp", isFromMetrics)
    );
    dispatch({
      type: TYPES.SET_SELECTED_OCP_FILTERS,
      payload: selectedFilters,
    });
  };
export const setOCPAppliedFilters = (navigate) => (dispatch, getState) => {
  const { start_date, end_date, selectedFilters } = getState().ocp;
  const appliedFilterArr = selectedFilters.filter((i) => i.value.length > 0);

  const appliedFilters = {};
  appliedFilterArr.forEach((item) => {
    appliedFilters[item["name"]] = item.value;
  });

  dispatch({
    type: TYPES.SET_OCP_APPLIED_FILTERS,
    payload: appliedFilters,
  });
  appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
  dispatch(applyFilters());
};

export const removeOCPAppliedFilters =
  (filterKey, filterValue, navigate) => (dispatch, getState) => {
    const appliedFilters = dispatch(
      deleteAppliedFilters(filterKey, filterValue, "ocp")
    );
    const { start_date, end_date } = getState().ocp;
    dispatch({
      type: TYPES.SET_OCP_APPLIED_FILTERS,
      payload: appliedFilters,
    });
    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);
    dispatch(applyFilters());
  };

export const setOCPDateFilter =
  (start_date, end_date, navigate) => (dispatch, getState) => {
    const appliedFilters = getState().ocp.appliedFilters;

    dispatch({
      type: TYPES.SET_OCP_DATE_FILTER,
      payload: {
        start_date,
        end_date,
      },
    });

    appendQueryString({ ...appliedFilters, start_date, end_date }, navigate);

    dispatch(fetchOCPJobs());
  };

export const setFilterFromURL = (searchParams) => ({
  type: TYPES.SET_OCP_APPLIED_FILTERS,
  payload: searchParams,
});

export const setOCPOtherSummaryFilter = () => (dispatch, getState) => {
  const results = [...getState().ocp.results];
  const keyWordArr = ["success", "failure"];
  const data = results.filter(
    (item) => !keyWordArr.includes(item.jobStatus?.toLowerCase())
  );
  // dispatch({
  //   type: TYPES.SET_OCP_FILTERED_DATA,
  //   payload: data,
  // });
  dispatch(tableReCalcValues());
};

export const getOCPSummary = (summary) => (dispatch) => {
  const countObj = {
    successCount: summary["success"],
    failureCount: summary["failure"],
    othersCount: 0,
    total: summary["total"],
  };
  for (const key in summary) {
    if (key !== "total" && key !== "success" && key !== "failure") {
      countObj["othersCount"] += summary[key];
    }
  }
  dispatch({
    type: TYPES.SET_OCP_SUMMARY,
    payload: countObj,
  });
};

export const fetchGraphData =
  (uuid, nodeName) => async (dispatch, getState) => {
    try {
      dispatch({ type: TYPES.GRAPH_LOADING });

      const graphData = getState().ocp.graphData;
      const hasData = graphData.filter((a) => a.uuid === uuid).length > 0;
      if (!hasData) {
        const response = await API.get(
          `${API_ROUTES.OCP_GRAPH_API_V1}/${uuid}`
        );

        if (response.status === 200) {
          dispatch({
            type: TYPES.SET_OCP_GRAPH_DATA,
            payload: { uuid, data: [[nodeName, response.data]] },
          });
        }
      }
    } catch (error) {
      dispatch(showFailureToast());
    }
    dispatch({ type: TYPES.GRAPH_COMPLETED });
  };

export const setTableColumns = (key, isAdding) => (dispatch, getState) => {
  let tableColumns = [...getState().ocp.tableColumns];
  const tableFilters = getState().ocp.tableFilters;

  if (isAdding) {
    const filterObj = tableFilters.find((item) => item.value === key);
    tableColumns.push(filterObj);
  } else {
    tableColumns = tableColumns.filter((item) => item.value !== key);
  }

  dispatch({
    type: TYPES.SET_OCP_COLUMNS,
    payload: tableColumns,
  });
};
export const tableReCalcValues = () => (dispatch, getState) => {
  const { page, perPage } = getState().ocp;

  const startIdx = page !== 1 ? (page - 1) * perPage : 0;
  const endIdx = page !== 1 ? page * perPage - 1 : perPage;
  //dispatch(setOCPPageOptions(page, perPage));
  dispatch(sliceOCPTableRows(startIdx, endIdx));
};

export const buildFilterData = () => async (dispatch, getState) => {
  try {
    const { tableFilters, categoryFilterValue } = getState().ocp;

    const params = dispatch(getRequestParams());

    const response = await API.get("/api/v1/ocp/filters", { params });
    if (response.status === 200 && response?.data?.filterData?.length > 0) {
      let data = cloneDeep(response.data.filterData);
      for (let i = 0; i < tableFilters.length; i++) {
        for (let j = 0; j < data.length; j++) {
          if (tableFilters[i]["value"] === data[j].key) {
            data[j]["name"] = tableFilters[i]["name"];
          }
        }
      }
      data.forEach((item) => {
        if (item["key"] === "ocpVersion") {
          item["name"] = "Version";
        }
      });
      await dispatch({
        type: TYPES.SET_OCP_FILTER_DATA,
        payload: data,
      });
      dispatch(getOCPSummary(response.data.summary));
      const activeFilter = categoryFilterValue || tableFilters[0].name;
      await dispatch(setOCPCatFilters(activeFilter));
    }
  } catch (error) {
    console.log(error);
  }
};
