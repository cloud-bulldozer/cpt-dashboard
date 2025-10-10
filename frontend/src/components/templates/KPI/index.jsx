import "./index.less";

import { useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";

import KPIDateFilter from "./KPIDateFilter";
import KPITable from "./KPITable";

function KPITab() {
  const dispatch = useDispatch();
  const hasFetchedRef = useRef(false);

  const kpiState = useSelector((state) => state.kpi || {});
  const { kpiData, isLoading, startDate, endDate } = kpiState;
  const fromSideMenu = useSelector((state) => state.sidemenu?.fromSideMenu || false);

  // Dynamically import actions to avoid potential circular dependencies
  const fetchKPIData = async (beginDate, endDate) => {
    const { fetchKPIData: fetchData } = await import("@/actions/kpiActions");
    dispatch(fetchData(beginDate, endDate));
  };

  const setKPIDateFilter = async (startDate, endDate) => {
    const { setKPIDateFilter: setFilter } = await import("@/actions/kpiActions");
    dispatch(setFilter(startDate, endDate));
  };

  const setFromSideMenuFlag = async (flag) => {
    const { setFromSideMenuFlag: setFlag } = await import("@/actions/sideMenuActions");
    dispatch(setFlag(flag));
  };

  useEffect(() => {
    if (!fromSideMenu && !kpiData && !hasFetchedRef.current) {
      fetchKPIData(startDate, endDate);
      hasFetchedRef.current = true;
    }
    if (fromSideMenu) {
      setFromSideMenuFlag(false);
    }
  }, [fromSideMenu, kpiData, startDate, endDate]);

  const handleDateFilterApply = (newStartDate, newEndDate) => {
    setKPIDateFilter(newStartDate, newEndDate);
    fetchKPIData(newStartDate, newEndDate);
  };

  return (
    <div className="kpi-table">
      <KPIDateFilter
        startDate={startDate}
        endDate={endDate}
        onApply={handleDateFilterApply}
      />
      {isLoading ? (
        <div className="loader">Loading KPI data...</div>
      ) : (
        kpiData && <KPITable data={kpiData} />
      )}
    </div>
  );
}

export default KPITab;
