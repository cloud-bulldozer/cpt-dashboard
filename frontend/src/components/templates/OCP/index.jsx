import {
  fetchGraphData,
  fetchOCPJobs,
  filterFromSummary,
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
  sliceOCPTableRows,
} from "@/actions/ocpActions.js";
import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@//components/organisms/MetricsTab";
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
  } = useSelector((state) => state.ocp);

  useEffect(() => {
    if (searchParams.size > 0) {
      // date filter is set apart
      const startDate = searchParams.get("start_date");
      const endDate = searchParams.get("end_date");

      searchParams.delete("start_date");
      searchParams.delete("end_date");
      const params = Object.fromEntries(searchParams);
      dispatch(setFilterFromURL(params));
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
    dispatch(removeAppliedFilters("jobStatus", navigate));
  };
  const applyStatusFilter = (value) => {
    dispatch(filterFromSummary("jobStatus", value, navigate));
  };
  const applyOtherFilter = () => {
    dispatch(removeAppliedFilters("jobStatus", navigate));
    dispatch(setOtherSummaryFilter());
  };

  /* Filter helper */

  const onCategoryChange = (_event, value) => {
    dispatch(setOCPCatFilters(value));
  };
  const onOptionsChange = (_event, value) => {
    dispatch(setAppliedFilters(value, navigate));
  };
  const deleteItem = (key) => {
    dispatch(removeAppliedFilters(key, navigate));
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
  return (
    <>
      <MetricsTab
        totalItems={filteredResults.length}
        summary={summary}
        removeStatusFilter={removeStatusFilter}
        applyStatusFilter={applyStatusFilter}
        applyOtherFilter={applyOtherFilter}
      />

      {tableFilters?.length > 0 && filterOptions?.length > 0 && (
        <TableFilter
          tableFilters={tableFilters}
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
        />
      )}

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
      />
    </>
  );
};

export default OCP;
