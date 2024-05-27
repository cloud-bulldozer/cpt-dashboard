import { ExpandableRowContent, Td, Tr } from "@patternfly/react-table";

import MetadataRow from "../MetaDataRow";
import Plotly from "react-plotly.js";
import TableCell from "../../atoms/TableCell";
import { uid } from "@/utils/helper.js";

const TableRows = (props) => {
  const { rows, columns, addExpansion } = props;
  const details = true;
  const getGraphData = (uuid) => {
    return props?.graphData?.filter((a) => a.uuid === uuid);
  };
  return (
    rows?.length > 0 &&
    rows.map((item, rowIndex) => (
      <>
        <Tr key={uid()}>
          {addExpansion && (
            <Td
              expand={
                details
                  ? {
                      rowIndex,
                      isExpanded: props?.isRunExpanded(item),
                      onToggle: () =>
                        props?.setRunExpanded(
                          item,
                          !props?.isRunExpanded(item)
                        ),
                      expandId: "expandable-row",
                    }
                  : undefined
              }
            />
          )}

          {columns.map((col) => (
            <TableCell key={uid()} col={col} item={item} />
          ))}
        </Tr>
        {addExpansion && (
          <Tr isExpanded={props?.isRunExpanded(item)}>
            <Td colSpan={4}>
              <ExpandableRowContent>
                <MetadataRow item={item} />
              </ExpandableRowContent>
            </Td>
            <Td colSpan={4}>
              <ExpandableRowContent className="myDiv">
                {props?.graphData[0] && (
                  <PlotGraph
                    data={props?.graphData[0]}
                    width={"10vw"}
                    height={"10vh"}
                  />
                )}
              </ExpandableRowContent>
            </Td>
          </Tr>
        )}
      </>
    ))
  );
};

export default TableRows;
export const PlotGraph = (props) => {
  console.log(props.data);
  return (
    <Plotly
      data={props?.data}
      useResizeHandler={true}
      layout={{ responsive: true, autosize: true }}
      //  style={{ width: props.width, height: props.height }}
    />
  );
};
