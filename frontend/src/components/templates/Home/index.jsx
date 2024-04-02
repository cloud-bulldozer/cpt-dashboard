import { useDispatch, useSelector } from "react-redux";

import TableLayout from "@/components/organisms/TableLayout";
import { fetchOCPJobsData } from "@/actions/homeActions.js";
import { useEffect } from "react";

const Home = () => {
  const dispatch = useDispatch();

  const { results, tableColumns } = useSelector((state) => state.cpt);

  useEffect(() => {
    dispatch(fetchOCPJobsData());
  }, [dispatch]);

  // const columnNames = {};
  // tableColumns.map((item) => (columnNames[item.value] = item.name));

  return (
    <>
      <TableLayout tableData={results} tableColumns={tableColumns} />
    </>
  );
};

export default Home;
