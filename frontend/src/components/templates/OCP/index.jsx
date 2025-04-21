import {
  buildFilterData,
  fetchGraphData,
  fetchOCPJobs,
  setFilterFromURL,
  setOCPDateFilter,
  setSelectedFilter,
  setSelectedFilterFromUrl,
  setTableColumns,
} from "@/actions/ocpActions";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@/components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { setFromSideMenuFlag } from "@/actions/sideMenuActions";

const OCP = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const hasFetchedRef = useRef(false);
  const {
    results,
    tableColumns,
    activeSortDir,
    activeSortIndex,
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
    totalJobs,
  } = useSelector((state) => state.ocp);

  const fromSideMenu = useSelector((state) => state.sidemenu.fromSideMenu);

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
      dispatch(setOCPDateFilter(startDate, endDate, navigate));
    }
  }, []);

  useEffect(() => {
    if (!fromSideMenu && results.length === 0 && !hasFetchedRef.current) {
      dispatch(fetchOCPJobs());
      dispatch(buildFilterData());
      hasFetchedRef.current = true;
    }
    if (fromSideMenu) {
      dispatch(setFromSideMenuFlag(false));
    }
  }, [dispatch, fromSideMenu, results]);

  //Filter Helper
  const modifidedTableFilters = useMemo(
    () =>
      tableFilters.filter(
        (item) => item.value !== "endDate" && item.value !== "startDate"
      ),
    [tableFilters]
  );
  const updateSelectedFilter = (category, value, isFromMetrics = false) => {
    dispatch(setSelectedFilter(category, value, isFromMetrics));
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
      dispatch(fetchGraphData(run.uuid, run.benchmark));
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
        type={"ocp"}
        appliedFilters={appliedFilters}
      />

      <TableFilter
        tableFilters={modifidedTableFilters}
        filterOptions={filterOptions}
        categoryFilterValue={categoryFilterValue}
        appliedFilters={appliedFilters}
        filterData={filterData}
        start_date={start_date}
        end_date={end_date}
        type={"ocp"}
        showColumnMenu={true}
        setColumns={setColumns}
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
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
        addExpansion={true}
        isRunExpanded={isRunExpanded}
        setRunExpanded={setRunExpanded}
        graphData={graphData}
        type={"ocp"}
        shouldSort={true}
      />
    </>
  );
};

export default OCP;
