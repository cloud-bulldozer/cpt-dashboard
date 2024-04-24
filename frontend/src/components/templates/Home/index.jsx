import {
  DEFAULT_PER_PAGE,
  START_PAGE,
} from "@/assets/constants/paginationConstants";
import {
  fetchOCPJobsData,
  setCPTSortDir,
  setCPTSortIndex,
  sliceTableRows,
  sortTable,
} from "@/actions/homeActions.js";
import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";

const Home = () => {
  const dispatch = useDispatch();

  const {
    results,
    tableColumns,
    activeSortDir,
    activeSortIndex,
    tableData,
    filterOptions,
  } = useSelector((state) => state.cpt);

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
        totalItems={results.length}
      />
    </>
  );
};

export default Home;
