import PropType from "prop-types";
import { uid } from "@/utils/helper";
import { useSelector } from "react-redux";
import { Table, Tbody, Th, Thead, Tr, Td } from "@patternfly/react-table";

const ILabSummary = (props) => {
  const { ids } = props;
  const { isSummaryLoading, summaryData } = useSelector((state) => state.ilab);

  const getSummaryData = (id) => {
    const data = summaryData?.find((a) => a.uid === id);
    return data;
  };
  const hasSummaryData = (ids) => {
    const hasData = Boolean(
      summaryData.filter((i) => ids.includes(i.uid)).length === ids.length
    );
    return hasData;
  };

  return (
    <div>
      {hasSummaryData(ids) ? (
        <Table
          variant="compact"
          className="box"
          key={uid()}
          aria-label="summary-table"
        >
          <Thead>
            <Tr>
              {ids.length > 1 ? <Th>Run</Th> : <></>}
              <Th>Metric</Th>
              <Th>Min</Th>
              <Th>Average</Th>
              <Th>Max</Th>
              <Th>Standard Deviation</Th>
            </Tr>
          </Thead>
          <Tbody>
            {ids.map((id, ridx) =>
              getSummaryData(id).data.map((stat, sidx) => (
                <Tr
                  hasNoInset
                  key={uid()}
                  {...(ridx % 2 === 0 && { isStriped: true })}
                >
                  {ids.length > 1 && sidx === 0 ? (
                    <Td rowSpan={getSummaryData(id).data.length}>{ridx + 1}</Td>
                  ) : undefined}
                  <Td>{stat.title}</Td>
                  <Td>
                    {typeof stat.min === "number"
                      ? stat.min.toPrecision(6)
                      : stat.min}
                  </Td>
                  <Td>
                    {typeof stat.avg === "number"
                      ? stat.avg.toPrecision(6)
                      : stat.avg}
                  </Td>
                  <Td>
                    {typeof stat.max === "number"
                      ? stat.max.toPrecision(6)
                      : stat.max}
                  </Td>
                  <Td>
                    {typeof stat.std_deviation === "number"
                      ? stat.std_deviation.toPrecision(6)
                      : stat.std_deviation}
                  </Td>
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      ) : isSummaryLoading && !hasSummaryData(ids) ? (
        <div className="loader"></div>
      ) : (
        <></>
      )}
    </div>
  );
};

ILabSummary.propTypes = {
  item: PropType.object,
};
export default ILabSummary;
