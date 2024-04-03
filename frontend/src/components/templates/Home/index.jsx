import {
  fetchOCPJobsData,
  setCPTSortDir,
  setCPTSortIndex,
} from "@/actions/homeActions.js";
import { useDispatch, useSelector } from "react-redux";

import TableLayout from "@/components/organisms/TableLayout";
import { useEffect } from "react";

const Home = () => {
  const dispatch = useDispatch();

  const { results, tableColumns, activeSortDir, activeSortIndex } = useSelector(
    (state) => state.cpt
  );

  useEffect(() => {
    dispatch(fetchOCPJobsData());
  }, [dispatch]);

  // const columnNames = {};
  // tableColumns.map((item) => (columnNames[item.value] = item.name));

  const setActiveSortDir = (dir) => {
    dispatch(setCPTSortDir(dir));
  };

  const setActiveSortIndex = (index) => {
    dispatch(setCPTSortIndex(index));
  };

  return (
    <>
      <TableLayout
        tableData={results}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        setActiveSortDir={setActiveSortDir}
        setActiveSortIndex={setActiveSortIndex}
      />
    </>
  );
};

export default Home;
