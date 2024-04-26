import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import {
  fetchOCPJobsData,
  removeAppliedFilters,
  setAppliedFilters,
  setCPTSortDir,
  setCPTSortIndex,
  setCatFilters,
  setDateFilter,
  setFilterFromURL,
  sliceTableRows,
  sortTable,
} from "@/actions/homeActions.js";
import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";

import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";

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
  } = useSelector((state) => state.cpt);

  useEffect(() => {
    if (searchParams.size > 0) {
      // date filter is set in fetchOCPJobsData()
      searchParams.delete("start_date");
      searchParams.delete("end_date");

      const params = Object.fromEntries(searchParams);
      dispatch(setFilterFromURL(params));
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
    dispatch(sortTable());
  };
  // Sorting
  // Pagination Helper
  const [perPage, setPerPage] = useState(DEFAULT_PER_PAGE);
  const [page, setPage] = useState(START_PAGE);

  const onSetPage = useCallback(
    (_evt, newPage, _perPage, startIdx, endIdx) => {
      setPage(newPage);
      dispatch(sliceTableRows(startIdx, endIdx));
    },
    [dispatch]
  );
  const onPerPageSelect = useCallback(
    (_evt, newPerPage, newPage, startIdx, endIdx) => {
      setPerPage(newPerPage);
      setPage(newPage);
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
  // Filter Helper
  return (
    <>
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
      />
    </>
  );
};

export default Home;
