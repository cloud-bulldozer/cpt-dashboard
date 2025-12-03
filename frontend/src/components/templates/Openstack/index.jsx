import { useEffect, useRef } from "react";
import { useInitFiltersFromURL } from "@/utils/hooks/useInitFiltersFromURL";
import { setFromSideMenuFlag } from "@/actions/sideMenuActions";

import { useDispatch, useSelector } from "react-redux";
import { fetchOSOJobs } from "@/actions/openstackActions.js";

import TableLayout from "@/components/organisms/TableLayout";

const OSOTab = () => {
  const dispatch = useDispatch();

  const hasFetchedRef = useRef(false);

  const {
    results,
    tableColumns,
    page,
    perPage,
    totalJobs,
    activeSortIndex,
    activeSortDir,
  } = useSelector((state) => state.oso);
  const fromSideMenu = useSelector((state) => state.sidemenu.fromSideMenu);

  useInitFiltersFromURL("oso");

  useEffect(() => {
    if (!fromSideMenu && results.length === 0 && !hasFetchedRef.current) {
      dispatch(fetchOSOJobs());

      hasFetchedRef.current = true;
    }
    if (fromSideMenu) {
      dispatch(setFromSideMenuFlag(false));
    }
    dispatch(fetchOSOJobs());
  }, [dispatch, fromSideMenu, results]);

  return (
    <>
      <TableLayout
        tableData={results}
        tableColumns={tableColumns}
        activeSortIndex={activeSortIndex}
        activeSortDir={activeSortDir}
        page={page}
        perPage={perPage}
        totalItems={totalJobs}
        addExpansion={false}
        type={"oso"}
        shouldSort={false}
      />
    </>
  );
};

export default OSOTab;
