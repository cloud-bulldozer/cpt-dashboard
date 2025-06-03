import {
  buildFilterData,
  fetchGraphData,
  fetchTelcoJobsData,
  setSelectedFilter,
  setTableColumns,
} from "@/actions/telcoActions.js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import MetricsTab from "@/components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { setFromSideMenuFlag } from "@/actions/sideMenuActions";
import { useInitFiltersFromURL } from "@/utils/hooks/useInitFiltersFromURL";
import { useNavigate } from "react-router-dom";

const Telco = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const hasFetchedRef = useRef(false);
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
    summary,
    graphData,
    totalJobs,
  } = useSelector((state) => state.telco);

  const fromSideMenu = useSelector((state) => state.sidemenu.fromSideMenu);

  useInitFiltersFromURL("telco");

  useEffect(() => {
    if (!fromSideMenu && results.length === 0 && !hasFetchedRef.current) {
      dispatch(fetchTelcoJobsData());
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
      dispatch(fetchGraphData(run.benchmark, run.uuid, run.encryptedData));
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
        type={"telco"}
        appliedFilters={appliedFilters}
      />
      <TableFilter
        tableFilters={modifidedTableFilters}
        filterOptions={filterOptions}
        filterData={filterData}
        categoryFilterValue={categoryFilterValue}
        appliedFilters={appliedFilters}
        start_date={start_date}
        end_date={end_date}
        type={"telco"}
        updateSelectedFilter={updateSelectedFilter}
        selectedFilters={selectedFilters}
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
        type={"telco"}
        addExpansion={true}
        isRunExpanded={isRunExpanded}
        setRunExpanded={setRunExpanded}
        graphData={graphData}
        shouldSort={true}
      />
    </>
  );
};

export default Telco;
