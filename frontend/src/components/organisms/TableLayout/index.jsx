import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

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
    setActiveSortIndex,
    setActiveSortDir,
    handleOnSort,
    page,
    perPage,
    setPage,
    setPerPage,
    onSetPage,
    onPerPageSelect,
    totalItems,
  } = props;

  const getSortParams = (columnIndex) => ({
    sortBy: {
      index: activeSortIndex,
      direction: activeSortDir,
      defaultDirection: "asc",
    },
    onSort: (_event, index, direction) => {
      setActiveSortIndex(index);
      setActiveSortDir(direction);
      handleOnSort();
    },
    columnIndex,
  });

  return (
    <>
      <Table isStriped>
        <Thead>
          <Tr>
            {tableColumns?.length > 0 &&
              tableColumns.map((col, idx) => (
                <Th key={uid()} sort={getSortParams(idx)}>
                  {col.name}
                </Th>
              ))}
          </Tr>
        </Thead>
        <Tbody>
          <TableRows rows={tableData} columns={tableColumns} />
        </Tbody>
      </Table>
      <RenderPagination
        items={totalItems}
        page={page}
        setPage={setPage}
        perPage={perPage}
        setPerPage={setPerPage}
        onSetPage={onSetPage}
        onPerPageSelect={onPerPageSelect}
      />
    </>
  );
};

TableLayout.propTypes = {
  tableData: PropTypes.array,
  tableColumns: PropTypes.array,
  activeSortIndex: PropTypes.number || PropTypes.object,
  activeSortDir: PropTypes.string || PropTypes.object,
  setActiveSortIndex: PropTypes.func,
  setActiveSortDir: PropTypes.func,
  handleOnSort: PropTypes.func,
  totalItems: PropTypes.number,
  page: PropTypes.number,
  perPage: PropTypes.number,
  onPerPageSelect: PropTypes.func,
  onSetPage: PropTypes.func,
  setPage: PropTypes.func,
  setPerPage: PropTypes.func,
};
export default TableLayout;
