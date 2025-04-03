import "./index.less";

import {
  ExpandableRowContent,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@patternfly/react-table";
import {
  fetchILabJobs,
  fetchMetricsInfo,
  fetchPeriods,
  setIlabDateFilter,
  toggleComparisonSwitch,
} from "@/actions/ilabActions";
import { formatDateTime, uid } from "@/utils/helper";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import IlabCompareComponent from "./IlabCompareComponent";
import IlabRowContent from "./IlabExpandedRow";
import RenderPagination from "@/components/organisms/Pagination";
import StatusCell from "./StatusCell";
import TableFilter from "@/components/organisms/TableFilters";

const ILab = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const {
    start_date,
    end_date,
    comparisonSwitch,
    tableData,
    page,
    perPage,
    totalItems,
  } = useSelector((state) => state.ilab);
  const [expandedResult, setExpandedResult] = useState([]);

  const isResultExpanded = (res) => expandedResult?.includes(res);
  const setExpanded = async (run, isExpanding = true) => {
    setExpandedResult((prevExpanded) => {
      const otherExpandedRunNames = prevExpanded.filter((r) => r !== run.id);
      return isExpanding
        ? [...otherExpandedRunNames, run.id]
        : otherExpandedRunNames;
    });
    if (isExpanding) {
      dispatch(fetchPeriods(run.id));
      dispatch(fetchMetricsInfo(run.id));
    }
  };

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
      dispatch(setIlabDateFilter(startDate, endDate, navigate));
    }
  }, []);

  useEffect(() => {
    dispatch(fetchILabJobs());
  }, [dispatch]);

  const columnNames = {
    benchmark: "Benchmark",
    email: "Email",
    name: "Name",
    source: "Source",
    metric: "Metric",
    begin_date: "Start Date",
    end_date: "End Date",
    status: "Status",
  };

  const onSwitchChange = () => {
    dispatch(toggleComparisonSwitch());
  };
  return (
    <>
      <TableFilter
        start_date={start_date}
        end_date={end_date}
        type={"ilab"}
        showColumnMenu={false}
        navigation={navigate}
        isSwitchChecked={comparisonSwitch}
        onSwitchChange={onSwitchChange}
      />
      {comparisonSwitch ? (
        <IlabCompareComponent />
      ) : (
        <>
          <Table aria-label="Misc table" isStriped variant="compact">
            <Thead>
              <Tr key={uid()}>
                <Th screenReaderText="Row expansion" />
                <Th>{columnNames.metric}</Th>
                <Th>{columnNames.begin_date}</Th>
                <Th>{columnNames.end_date}</Th>
                <Th>{columnNames.status}</Th>
              </Tr>
            </Thead>
            <Tbody>
              {tableData.map((item, rowIndex) => (
                <>
                  <Tr key={uid()}>
                    <Td
                      expand={{
                        rowIndex,
                        isExpanded: isResultExpanded(item.id),
                        onToggle: () =>
                          setExpanded(item, !isResultExpanded(item.id)),
                        expandId: `expandId-${uid()}`,
                      }}
                    />

                    <Td>{item.primary_metrics[0]}</Td>
                    <Th>{formatDateTime(item.begin_date)}</Th>
                    <Th>{formatDateTime(item.end_date)}</Th>
                    <Td>
                      <StatusCell value={item.status} />
                    </Td>
                  </Tr>
                  <Tr key={uid()} isExpanded={isResultExpanded(item.id)}>
                    <Td colSpan={8}>
                      <ExpandableRowContent>
                        <IlabRowContent item={item} />
                      </ExpandableRowContent>
                    </Td>
                  </Tr>
                </>
              ))}
            </Tbody>
          </Table>
          <RenderPagination
            items={totalItems}
            page={page}
            perPage={perPage}
            type={"ilab"}
          />
        </>
      )}
    </>
  );
};

export default ILab;
