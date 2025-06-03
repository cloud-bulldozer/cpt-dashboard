import {
  fetchDataConcurrently,
  setSelectedFilter,
} from "@/actions/homeActions.js";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useRef } from "react";

import MetricsTab from "@//components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { setFromSideMenuFlag } from "@/actions/sideMenuActions";
import { useInitFiltersFromURL } from "@/utils/hooks/useInitFiltersFromURL";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const dispatch = useDispatch();

  const navigate = useNavigate();
  const hasFetchedRef = useRef(false);
  const fromSideMenu = useSelector((state) => state.sidemenu.fromSideMenu);

  const {
    tableData,
    tableColumns,
    activeSortDir,
    activeSortIndex,
    results,
    filterData,
    filterOptions,
    tableFilters,
    categoryFilterValue,
    appliedFilters,
    start_date,
    end_date,
    page,
    perPage,
    summary,
    selectedFilters,
    totalJobs,
  } = useSelector((state) => state.cpt);

  useInitFiltersFromURL("cpt");
  useEffect(() => {
    if (!fromSideMenu && results.length === 0 && !hasFetchedRef.current) {
      dispatch(fetchDataConcurrently());
      hasFetchedRef.current = true;
    }
    if (fromSideMenu) {
      dispatch(setFromSideMenuFlag(false));
    }
  }, [dispatch, fromSideMenu, results]);
  // Filter Helper
  const updateSelectedFilter = (category, value, isFromMetrics) => {
    dispatch(setSelectedFilter(category, value, isFromMetrics));
  };
  // Filter Helper
  return (
    <>
      <MetricsTab
        totalItems={totalJobs}
        summary={summary}
        updateSelectedFilter={updateSelectedFilter}
        navigation={navigate}
        type={"cpt"}
        appliedFilters={appliedFilters}
      />

      <TableFilter
        tableFilters={tableFilters}
        filterOptions={filterOptions}
        categoryFilterValue={categoryFilterValue}
        filterData={filterData}
        appliedFilters={appliedFilters}
        start_date={start_date}
        end_date={end_date}
        type={"cpt"}
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
        showColumnMenu={false}
        navigation={navigate}
      />

      <TableLayout
        tableData={tableData}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        page={page}
        perPage={perPage}
        totalItems={totalJobs}
        addExpansion={false}
        type={"cpt"}
        shouldSort={false}
      />
    </>
  );
};

export default Home;
