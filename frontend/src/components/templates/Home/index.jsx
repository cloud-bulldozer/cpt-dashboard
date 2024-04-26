import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import {
  fetchOCPJobsData,
  setCPTSortDir,
  setCPTSortIndex,
  setFilterFromURL,
  sliceTableRows,
  sortTable,
} from "@/actions/homeActions.js";
import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { useSearchParams } from "react-router-dom";

const Home = () => {
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();

  const {
    filteredResults,
    tableColumns,
    activeSortDir,
    activeSortIndex,
    tableData,
    filterOptions,
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

  return (
    <>
      {filterOptions?.length > 0 && <TableFilter />}

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
