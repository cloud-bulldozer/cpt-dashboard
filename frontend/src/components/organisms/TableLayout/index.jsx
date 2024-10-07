import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";
import {
  handleOnSort,
  setActiveSortDir,
  setActiveSortIndex,
} from "@/actions/sortingActions";

import PropTypes from "prop-types";
import RenderPagination from "@/components/organisms/Pagination";
import TableRows from "@/components/molecules/TableRows";
import { uid } from "@/utils/helper.js";

const TableLayout = (props) => {
  const {
    tableData,
    tableColumns,
    activeSortIndex,
    activeSortDir,
    page,
    perPage,
    totalItems,
    addExpansion,
    type,
  } = props;

  const getSortParams = (columnIndex, colName) => ({
    sortBy: {
      index: activeSortIndex,
      direction: activeSortDir,
      defaultDirection: "asc",
    },
    onSort: (_event, index, direction) => {
      setActiveSortIndex(index, type);
      setActiveSortDir(direction, type);
      handleOnSort(colName, type);
    },
    columnIndex,
  });
  return (
    <>
      <Table isStriped>
        <Thead>
          <Tr>
            {addExpansion && <Th />}

            {tableColumns?.length > 0 &&
              tableColumns.map((col, idx) => (
                <Th key={uid()} sort={getSortParams(idx, col.value)}>
                  {col.name}
                </Th>
              ))}
          </Tr>
        </Thead>
        {!addExpansion ? (
          <Tbody>
            <TableRows
              rows={tableData}
              columns={tableColumns}
              addExpansion={addExpansion}
              isRunExpanded={props?.isRunExpanded}
              setRunExpanded={props?.setRunExpanded}
              graphData={props?.graphData}
              type={props.type}
            />
          </Tbody>
        ) : (
          <TableRows
            rows={tableData}
            columns={tableColumns}
            addExpansion={addExpansion}
            isRunExpanded={props?.isRunExpanded}
            setRunExpanded={props?.setRunExpanded}
            graphData={props?.graphData}
            type={props.type}
          />
        )}
      </Table>
      <RenderPagination
        items={totalItems}
        page={page}
        perPage={perPage}
        type={props.type}
        pageTopRef={props.pageTopRef}
      />
    </>
  );
};

TableLayout.propTypes = {
  tableData: PropTypes.array,
  tableColumns: PropTypes.array,
  activeSortIndex: PropTypes.number || PropTypes.object,
  activeSortDir: PropTypes.string || PropTypes.object,
  totalItems: PropTypes.number,
  page: PropTypes.number,
  perPage: PropTypes.number,
  addExpansion: PropTypes.bool,
  graphData: PropTypes.array,
  type: PropTypes.string,
  isRunExpanded: PropTypes.func,
  setRunExpanded: PropTypes.func,
  pageTopRef: PropTypes.oneOfType([
    PropTypes.func, // for legacy refs
    PropTypes.shape({ current: PropTypes.instanceOf(Element) }),
  ]),
};
export default TableLayout;
