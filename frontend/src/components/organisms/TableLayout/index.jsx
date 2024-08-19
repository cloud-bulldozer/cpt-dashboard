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

  const getSortParams = (columnIndex) => ({
    sortBy: {
      index: activeSortIndex,
      direction: activeSortDir,
      defaultDirection: "asc",
    },
    onSort: (_event, index, direction) => {
      setActiveSortIndex(index, type);
      setActiveSortDir(direction, type);
      handleOnSort(type);
    },
    columnIndex,
  });

  return (
    <>
      <Table isStriped>
        <Thead>
          <Tr>
            {addExpansion && <Th screenReaderText="Row expansion" />}

            {tableColumns?.length > 0 &&
              tableColumns.map((col, idx) => (
                <Th key={uid()} sort={getSortParams(idx)}>
                  {col.name}
                </Th>
              ))}
          </Tr>
        </Thead>
        <Tbody isExpanded={addExpansion}>
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
      </Table>
      <RenderPagination
        items={totalItems}
        page={page}
        perPage={perPage}
        type={props.type}
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
};
export default TableLayout;
