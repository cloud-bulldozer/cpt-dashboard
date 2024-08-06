import {
  fetchOCPJobsData,
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
  setSelectedFilter,
  setSelectedFilterFromUrl,
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
    selectedFilters,
  } = useSelector((state) => state.cpt);

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
  const onOptionsChange = () => {
    dispatch(setAppliedFilters(navigate));
  };
  const deleteItem = (key, value) => {
    dispatch(removeAppliedFilters(key, value, navigate));
    updateSelectedFilter(key, value, false);
  };
  const startDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(date, key, navigate));
  };
  const endDateChangeHandler = (date, key) => {
    dispatch(setDateFilter(key, date, navigate));
  };
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
  const updateSelectedFilter = (category, value, isFromMetrics) => {
    dispatch(setSelectedFilter(category, value, isFromMetrics));
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
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
        showColumnMenu={false}
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
        addExpansion={false}
        state={"cpt"}
      />
    </>
  );
};

export default Home;
