import {
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@patternfly/react-icons";
import {
  ExpandableRowContent,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@patternfly/react-table";
import { Grid, GridItem, Label } from "@patternfly/react-core";
import { fetchGraphData, fetchILabJobs } from "@/actions/ilabActions";
import { formatDateTime, uid } from "@/utils/helper";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";

import Plot from "react-plotly.js";
import TableFilter from "@/components/organisms/TableFilters";
import { useNavigate } from "react-router-dom";
import { cloneDeep } from "lodash";

const ILab = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { results, start_date, end_date, graphData } = useSelector(
    (state) => state.ilab
  );
  const isGraphLoading = useSelector((state) => state.loading.isGraphLoading);

  const [expandedResult, setExpandedResult] = useState([]);

  const isResultExpanded = (res) => expandedResult?.includes(res);
  const setExpanded = (run, isExpanding = true) => {
    setExpandedResult((prevExpanded) => {
      const otherExpandedRunNames = prevExpanded.filter((r) => r !== run.id);
      return isExpanding
        ? [...otherExpandedRunNames, run.id]
        : otherExpandedRunNames;
    });
    if (isExpanding) {
      dispatch(fetchGraphData(run.id, run?.primary_metrics[0]));
    }
  };

  const getGraphData = (id) => {
    const data = graphData?.filter((a) => a.uid === id);
    return cloneDeep(data);
  };
  const hasGraphData = (uuid) => {
    const hasData = getGraphData(uuid).length > 0;

    return hasData;
  };

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

  const StatusCell = (props) => {
    return props.value?.toLowerCase() === "pass" ? (
      <Label color="green" icon={<CheckCircleIcon />}>
        Success
      </Label>
    ) : (
      <Label color="red" icon={<ExclamationCircleIcon />}>
        Failure
      </Label>
    );
  };

  const RenderKey = (props) => {
    const { value } = props;
    return (
      <>
        {Object.keys(value).length > 0 &&
          Object.keys(value).map((unit) => {
            return (
              <>
                <span>
                  {" "}
                  {value[unit]} {""}
                </span>
              </>
            );
          })}
      </>
    );
  };

  return (
    <>
      <TableFilter
        start_date={start_date}
        end_date={end_date}
        type={"ilab"}
        showColumnMenu={false}
        navigation={navigate}
      />
      <Table aria-label="Misc table" isStriped>
        <Thead>
          <Tr>
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
              <Tr isExpanded={isResultExpanded(item.id)}>
                <Td colSpan={8}>
                  <ExpandableRowContent>
                    <Grid hasGutter>
                      <GridItem span={4}>
                        <strong>
                          <em>Tags</em>
                        </strong>
                        {Object.keys(item.tags).length > 0 &&
                          Object.keys(item.tags).map((key) => (
                            <>
                              <div>
                                <strong key={uid()}>{key}</strong>:{" "}
                                {item.tags[key]}
                              </div>
                            </>
                          ))}
                      </GridItem>
                      <GridItem span={4}>
                        <strong>
                          <em>Parameters</em>
                        </strong>
                        {Object.keys(item.params).length > 0 &&
                          Object.keys(item.params).map((key) => (
                            <>
                              <div>
                                <strong key={uid()}>{key}</strong>:{" "}
                                {item.params[key]}
                              </div>
                            </>
                          ))}
                      </GridItem>
                      <GridItem span={8}>
                        {isGraphLoading && !hasGraphData(item.id) ? (
                          <div className="loader"></div>
                        ) : (
                          <>
                            <Plot
                              data={getGraphData(item.id)[0]?.data}
                              layout={getGraphData(item.id)[0]?.layout}
                              key={uid()}
                            />
                          </>
                        )}
                      </GridItem>
                    </Grid>
                  </ExpandableRowContent>
                </Td>
              </Tr>
            </>
          ))}
        </Tbody>
      </Table>
    </>
  );
};

export default ILab;
