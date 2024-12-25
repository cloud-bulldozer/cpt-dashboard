import {
  buildFilterData,
  fetchGraphData,
  fetchQuayJobsData,
  setFilterFromURL,
  setQuayDateFilter,
  setSelectedFilter,
  setSelectedFilterFromUrl,
  setTableColumns,
} from "@/actions/quayActions.js";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@/components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";

const Quay = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const {
    results,
    tableColumns,
    activeSortIndex,
    activeSortDir,
    page,
    perPage,
    tableFilters,
    filterOptions,
    categoryFilterValue,
    filterData,
    appliedFilters,
    start_date,
    end_date,
    selectedFilters,
    graphData,
    summary,
    totalJobs,
  } = useSelector((state) => state.quay);

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
      dispatch(setQuayDateFilter(startDate, endDate, navigate));
    }
  }, []);

  useEffect(() => {
    dispatch(buildFilterData());
    dispatch(fetchQuayJobsData());
  }, [dispatch]);

  //Filter Helper
  const modifidedTableFilters = useMemo(
    () =>
      tableFilters.filter(
        (item) => item.value !== "endDate" && item.value !== "startDate"
      ),
    [tableFilters]
  );
  const updateSelectedFilter = (category, value, isFromMetrics) => {
    dispatch(setSelectedFilter(category, value, isFromMetrics));
  };
  //Filter Helper
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
        totalItems={totalJobs}
        summary={summary}
        updateSelectedFilter={updateSelectedFilter}
        navigation={navigate}
        type={"quay"}
        appliedFilters={appliedFilters}
      />
      <TableFilter
        tableFilters={modifidedTableFilters}
        filterOptions={filterOptions}
        categoryFilterValue={categoryFilterValue}
        filterData={filterData}
        appliedFilters={appliedFilters}
        start_date={start_date}
        end_date={end_date}
        type={"quay"}
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
        showColumnMenu={true}
        setColumns={setColumns}
        navigation={navigate}
      />
      <TableLayout
        tableData={results}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        page={page}
        perPage={perPage}
        totalItems={totalJobs}
        type={"quay"}
        addExpansion={true}
        isRunExpanded={isRunExpanded}
        setRunExpanded={setRunExpanded}
        graphData={graphData}
        shouldSort={true}
      />
    </>
  );
};

export default Quay;
