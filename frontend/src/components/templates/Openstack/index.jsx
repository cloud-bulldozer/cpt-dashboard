import { useEffect, useRef, useMemo, useState, useCallback } from "react";
import { useInitFiltersFromURL } from "@/utils/hooks/useInitFiltersFromURL";
import { setFromSideMenuFlag } from "@/actions/sideMenuActions";

import { useDispatch, useSelector } from "react-redux";
import {
  fetchOSOJobs,
  setSelectedFilter,
  buildFilterData,
  setTableColumns,
} from "@/actions/openstackActions.js";
import { useNavigate } from "react-router-dom";

import MetricsTab from "@/components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";

import TableLayout from "@/components/organisms/TableLayout";

const OSOTab = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const hasFetchedRef = useRef(false);

  const {
    results,
    tableColumns,
    page,
    perPage,
    totalJobs,
    activeSortIndex,
    activeSortDir,
    tableFilters,
    filterOptions,
    start_date,
    end_date,
    appliedFilters,
    filterData,
    categoryFilterValue,
    selectedFilters,
    summary,
  } = useSelector((state) => state.oso);
  const fromSideMenu = useSelector((state) => state.sidemenu.fromSideMenu);

  useInitFiltersFromURL("oso");

  useEffect(() => {
    if (!fromSideMenu && results.length === 0 && !hasFetchedRef.current) {
      dispatch(fetchOSOJobs());
      dispatch(buildFilterData());
      hasFetchedRef.current = true;
    }
    if (fromSideMenu) {
      dispatch(setFromSideMenuFlag(false));
    }
    dispatch(fetchOSOJobs());
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
  const setColumns = (value, isAdding) => {
    dispatch(setTableColumns(value, isAdding));
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
  };

  const isRunExpanded = useCallback(
    (run) => expandedRunNames.includes(run.uuid),
    [expandedRunNames]
  );
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
        type={"oso"}
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
        type={"oso"}
        shouldSort={false}
      />
    </>
  );
};

export default OSOTab;
