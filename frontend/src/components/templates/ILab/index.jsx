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
  fetchIlabFilters,
  fetchIlabJobs,
  fetchRowAPIs,
  toggleComparisonSwitch,
  updateURL,
} from "@/actions/ilabActions";
import { formatDateTime, uid } from "@/utils/helper";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import IlabCompareComponent from "./IlabCompareComponent";
import IlabRowContent from "./IlabExpandedRow";
import RenderPagination from "@/components/organisms/Pagination";
import StatusCell from "./StatusCell";
import TableFilter from "@/components/organisms/TableFilters";
import { useInitFiltersFromURL } from "@/utils/hooks/useInitFiltersFromURL";
import { useNavigate } from "react-router-dom";

const ILab = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const {
    results,
    tableFilters,
    filterOptions,
    categoryFilterValue,
    filterData,
    appliedFilters,
    start_date,
    end_date,
    selectedFilters,
    totalItems,
    comparisonSwitch,
    page,
    perPage,
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
    if (isExpanding && !isResultExpanded(run.id)) {
      dispatch(fetchRowAPIs(run));
    }
  };

  useInitFiltersFromURL("ilab");

  useEffect(() => {
    dispatch(fetchIlabJobs());
    dispatch(fetchIlabFilters());
  }, [dispatch, navigate]);

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

  //Filter Helper
  const modifiedTableFilters = useMemo(
    () =>
      tableFilters.filter(
        (item) => item.value !== "endDate" && item.value !== "startDate"
      ),
    [tableFilters]
  );
  const updateSelectedFilter = () => {};

  const onSwitchChange = useCallback(() => {
    dispatch(toggleComparisonSwitch());
    dispatch(updateURL(navigate));
  }, [dispatch, navigate]);
  return (
    <div className="ilab-table-container">
      <TableFilter
        tableFilters={modifiedTableFilters}
        filterOptions={filterOptions}
        categoryFilterValue={categoryFilterValue}
        appliedFilters={appliedFilters}
        filterData={filterData}
        start_date={start_date}
        end_date={end_date}
        selectedFilters={selectedFilters}
        updateSelectedFilter={updateSelectedFilter}
        navigation={navigate}
        type={"ilab"}
        showColumnMenu={false}
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
              {results.map((item, rowIndex) => (
                <>
                  <Tr key={item.id}>
                    <Td
                      expand={{
                        rowIndex,
                        isExpanded: isResultExpanded(item.id),
                        onToggle: () =>
                          setExpanded(item, !isResultExpanded(item.id)),
                        expandId: `expandId-${item.id}`,
                      }}
                    />
                    <Td>{item.primary_metrics[0]}</Td>
                    <Th>{formatDateTime(item.begin_date)}</Th>
                    <Th>{formatDateTime(item.end_date)}</Th>
                    <Td>
                      <StatusCell value={item.status} />
                    </Td>
                  </Tr>
                  <Tr
                    key={`${item.id}-exp`}
                    isExpanded={isResultExpanded(item.id)}
                  >
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
    </div>
  );
};

export default ILab;
