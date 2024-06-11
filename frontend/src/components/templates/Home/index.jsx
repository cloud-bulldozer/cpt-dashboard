import {
  fetchOCPJobsData,
  filterFromSummary,
  removeAppliedFilters,
  setAppliedFilters,
  setCPTSortDir,
  setCPTSortIndex,
  setCatFilters,
  setDateFilter,
  setFilterFromURL,
  setOtherSummaryFilter,
  setPage,
  setPageOptions,
  sliceTableRows,
} from "@/actions/homeActions.js";
import { useCallback, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@//components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { sortTable } from "@/actions/commonActions";

const Home = () => {
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const {
    filteredResults,
    tableColumns,
    activeSortDir,
    activeSortIndex,
    tableData,
    filterOptions,
    tableFilters,
    categoryFilterValue,
    filterData,
    appliedFilters,
    start_date,
    end_date,
    page,
    perPage,
    summary,
  } = useSelector((state) => state.cpt);

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
    dispatch(fetchOCPJobsData());
  }, [dispatch]);
  //Sorting
  const setActiveSortDir = (dir) => {
    dispatch(setCPTSortDir(dir));
  };
  const setActiveSortIndex = (index) => {
    dispatch(setCPTSortIndex(index));
  };
  const handleOnSort = () => {
    dispatch(sortTable("cpt"));
  };
  // Sorting

  // Pagination Helper
  const onSetPage = useCallback(
    (_evt, newPage, _perPage, startIdx, endIdx) => {
      dispatch(setPage(newPage));
      dispatch(sliceTableRows(startIdx, endIdx));
    },
    [dispatch]
  );
  const onPerPageSelect = useCallback(
    (_evt, newPerPage, newPage, startIdx, endIdx) => {
      dispatch(setPageOptions(newPage, newPerPage));
      dispatch(sliceTableRows(startIdx, endIdx));
    },
    [dispatch]
  );
  // Pagination helper

  // Filter Helper
  const onCategoryChange = (_event, value) => {
    dispatch(setCatFilters(value));
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
  // Filter Helper
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
          type={"cpt"}
          showColumnMenu={false}
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
        addExpansion={false}
        state={"cpt"}
      />
    </>
  );
};

export default Home;
