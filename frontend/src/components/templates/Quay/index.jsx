import { useDispatch, useSelector } from "react-redux";

import TableFilter from "@/components/organisms/TableFilters";
import TableLayout from "@/components/organisms/TableLayout";
import { fetchQuayJobsData } from "@/actions/quayActions.js";
import { useEffect } from "react";

const Quay = () => {
  const dispatch = useDispatch();

  const {
    tableData,
    tableColumns,
    activeSortIndex,
    activeSortDir,
    page,
    perPage,
    filteredResults,
  } = useSelector((state) => state.quay);

  useEffect(() => {
    dispatch(fetchQuayJobsData());
  }, [dispatch]);

  return (
    <>
      <TableLayout
        tableData={tableData}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        page={page}
        perPage={perPage}
        totalItems={filteredResults.length}
        type={"quay"}
        addExpansion={false}
      />
    </>
  );
};

export default Quay;
