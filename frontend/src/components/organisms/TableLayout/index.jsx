import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";
import {
  handleOnSort,
  setActiveSortDir,
  setActiveSortIndex,
} from "@/actions/sortingActions";

import CustomEmptyState from "@/components/molecules/EmptyState";
import PropTypes from "prop-types";
import RenderPagination from "@/components/organisms/Pagination";
import TableRows from "@/components/molecules/TableRows";
import { isEmptyObject } from "@/utils/helper.js";
import { useSelector } from "react-redux";

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
    shouldSort,
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
  const isLoading = useSelector((state) => state.loading.isLoading);

  const appliedFilters = useSelector(
    (state) => state[props.type].appliedFilters
  );
  const isFilterApplied = !isEmptyObject(appliedFilters);
  return (
    <>
      {!isLoading && tableData.length === 0 ? (
        <CustomEmptyState type={isFilterApplied ? "noFilterData" : "noData"} />
      ) : (
        <>
          <Table isStriped ouiaId="main_data_table">
            <Thead>
              <Tr>
                {addExpansion && <Th />}

                {tableColumns?.length > 0 &&
                  tableColumns.map((col, idx) => (
                    <Th
                      key={`${col.value}-${idx}`}
                      sort={shouldSort ? getSortParams(idx, col.value) : ""}
                    >
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
          />
        </>
      )}
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
  shouldSort: PropTypes.bool,
};
export default TableLayout;
