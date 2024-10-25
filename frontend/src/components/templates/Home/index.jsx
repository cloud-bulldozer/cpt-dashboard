import {
  fetchOCPJobsData,
  setCPTDateFilter,
  setFilterFromURL,
  setSelectedFilter,
  setSelectedFilterFromUrl,
} from "@/actions/homeActions.js";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import MetricsTab from "@//components/organisms/MetricsTab";
import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { useEffect } from "react";

const Home = () => {
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const {
    tableColumns,
    activeSortDir,
    activeSortIndex,
    results,
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
    totalJobs,
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
      dispatch(setCPTDateFilter(startDate, endDate, navigate));
    }
  }, []);

  useEffect(() => {
    dispatch(fetchOCPJobsData());
  }, [dispatch]);
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
        tableData={results}
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
