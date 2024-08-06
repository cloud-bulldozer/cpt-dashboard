import {
  fetchGraphData,
  fetchOCPJobs,
  removeAppliedFilters,
  setAppliedFilters,
  setDateFilter,
  setFilterFromURL,
  setOCPCatFilters,
  setOCPSortDir,
  setOCPSortIndex,
  setOtherSummaryFilter,
  setPage,
  setPageOptions,
  setSelectedFilter,
  setSelectedFilterFromUrl,
  setTableColumns,
  sliceOCPTableRows,
} from "@/actions/ocpActions";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@/components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { sortTable } from "@/actions/commonActions.js";

const OCP = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const {
    filteredResults,
    tableColumns,
    activeSortDir,
    activeSortIndex,
    tableData,
    page,
    perPage,
    summary,
    tableFilters,
    filterOptions,
    categoryFilterValue,
    filterData,
    appliedFilters,
    start_date,
    end_date,
    graphData,
    selectedFilters,
  } = useSelector((state) => state.ocp);

  const modifidedTableFilters = useMemo(
    () =>
      tableFilters.filter(
        (item) => item.value !== "endDate" && item.value !== "startDate"
      ),
    [tableFilters]
  );
  useEffect(() => {
    if (searchParams.size > 0) {
      // date filter is set apart
      const startDate = searchParams.get("start_date");
      const endDate = searchParams.get("end_date");

      searchParams.delete("start_date");
      searchParams.delete("end_date");
      const params = Object.fromEntries(searchParams);
      const obj = {};
      for (const key in params) {
        obj[key] = params[key].split(",");
      }
      dispatch(setFilterFromURL(obj));
      dispatch(setSelectedFilterFromUrl(params));
      dispatch(setDateFilter(startDate, endDate, navigate));
    }
  }, []);

  useEffect(() => {
    dispatch(fetchOCPJobs());
  }, [dispatch]);

  //Sorting
  const setActiveSortDir = (dir) => {
    dispatch(setOCPSortDir(dir));
  };
  const setActiveSortIndex = (index) => {
    dispatch(setOCPSortIndex(index));
  };
  const handleOnSort = () => {
    dispatch(sortTable("ocp"));
  };
  // Sorting

  // Pagination Helper
  const onSetPage = useCallback(
    (_evt, newPage, _perPage, startIdx, endIdx) => {
      dispatch(setPage(newPage));
      dispatch(sliceOCPTableRows(startIdx, endIdx));
    },
    [dispatch]
  );
  const onPerPageSelect = useCallback(
    (_evt, newPerPage, newPage, startIdx, endIdx) => {
      dispatch(setPageOptions(newPage, newPerPage));
      dispatch(sliceOCPTableRows(startIdx, endIdx));
    },
    [dispatch]
  );
  // Pagination helper
  /* Summary Tab Filter*/
  const removeStatusFilter = () => {
    if (
      Array.isArray(appliedFilters["jobStatus"]) &&
      appliedFilters["jobStatus"].length > 0
    ) {
      appliedFilters["jobStatus"].forEach((element) => {
        updateSelectedFilter("jobStatus", element, true);
        dispatch(removeAppliedFilters("jobStatus", element, navigate));
      });
    }
  };
  const applyStatusFilter = (value) => {
    updateSelectedFilter("jobStatus", value, true);
    dispatch(setAppliedFilters(navigate));
  };
  const applyOtherFilter = () => {
    removeStatusFilter();
    dispatch(setOtherSummaryFilter());
  };
  const updateSelectedFilter = (category, value, isFromMetrics = false) => {
    dispatch(setSelectedFilter(category, value, isFromMetrics));
  };

  /* Filter helper */

  const onCategoryChange = (_event, value) => {
    dispatch(setOCPCatFilters(value));
  };
  const onOptionsChange = () => {
    dispatch(setAppliedFilters(navigate));
  };
  const deleteItem = (key, value) => {
    dispatch(removeAppliedFilters(key, value, navigate));
    updateSelectedFilter(key, value);
  };
  const startDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(date, key, navigate));
  };
  const endDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(key, date, navigate));
  };
  //Row expansion
  const [expandedRunNames, setExpandedRunNames] = useState([]);
  const setRunExpanded = (run, isExpanding = true) => {
    setExpandedRunNames((prevExpanded) => {
      const otherExpandedRunNames = prevExpanded.filter((r) => r !== run.uuid);
      return isExpanding
        ? [...otherExpandedRunNames, run.uuid]
        : otherExpandedRunNames;
    });
    if (isExpanding) {
      dispatch(fetchGraphData(run.uuid));
    }
  };

  const isRunExpanded = useCallback(
    (run) => expandedRunNames.includes(run.uuid),
    [expandedRunNames]
  );
  const setColumns = (value, isAdding) => {
    dispatch(setTableColumns(value, isAdding));
  };
  return (
    <>
      <MetricsTab
        totalItems={filteredResults.length}
        summary={summary}
        removeStatusFilter={removeStatusFilter}
        applyStatusFilter={applyStatusFilter}
        applyOtherFilter={applyOtherFilter}
      />

      <TableFilter
        tableFilters={modifidedTableFilters}
        filterOptions={filterOptions}
        categoryFilterValue={categoryFilterValue}
        filterData={filterData}
        appliedFilters={appliedFilters}
        start_date={start_date}
        end_date={end_date}
        onCategoryChange={onCategoryChange}
        onOptionsChange={onOptionsChange}
        deleteItem={deleteItem}
        startDateChangeHandler={startDateChangeHandler}
        endDateChangeHandler={endDateChangeHandler}
        type={"ocp"}
        showColumnMenu={true}
        setColumns={setColumns}
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
      />

      <TableLayout
        tableData={tableData}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        setActiveSortDir={setActiveSortDir}
        setActiveSortIndex={setActiveSortIndex}
        handleOnSort={handleOnSort}
        onPerPageSelect={onPerPageSelect}
        onSetPage={onSetPage}
        page={page}
        perPage={perPage}
        totalItems={filteredResults.length}
        addExpansion={true}
        isRunExpanded={isRunExpanded}
        setRunExpanded={setRunExpanded}
        graphData={graphData}
        type={"ocp"}
      />
    </>
  );
};

export default OCP;
