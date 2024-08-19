import { useDispatch, useSelector } from "react-redux";

import TableLayout from "@/components/organisms/TableLayout";
import { fetchTelcoJobsData } from "@/actions/telcoActions.js";
import { useEffect } from "react";

const Telco = () => {
  const dispatch = useDispatch();
  const {
    tableData,
    tableColumns,
    activeSortIndex,
    activeSortDir,
    page,
    perPage,
    filteredResults,
  } = useSelector((state) => state.telco);

  useEffect(() => {
    dispatch(fetchTelcoJobsData());
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
        type={"telco"}
        addExpansion={false}
      />
    </>
  );
};

export default Telco;
