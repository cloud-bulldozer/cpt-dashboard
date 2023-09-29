
import {Table, Thead, Tr, Th, Tbody, Td} from '@patternfly/react-table';
import {Puff} from "react-loading-icons";
import React from "react";

export const TableView = ({columns , rows = [], initialState = true, stickyHeader=false, ...props  }) => {
    // index of the currently active column
    const [activeSortIndex, setActiveSortIndex] = React.useState(-1);
    // sort direction of the currently active column
    const [activeSortDirection, setActiveSortDirection] = React.useState('none');

    const onSort = (event, index, direction) => {
        setActiveSortIndex(index);
        setActiveSortDirection(direction);
        // sorts the rows
        const updatedRows = rows.sort((a, b) => {
            if (typeof a[index].props.value === 'number') {
            // numeric sort
            if (direction === 'asc') {
                return a[index].props.value - b[index].props.value;
            }
            return b[index].props.value - a[index].props.value;
            } else if (new Date(a[index].props.value).toString() !== "Invalid Date") {
            if (direction === 'asc') {
                return new Date(a[index].props.value) - new Date(b[index].props.value)
            }
            return new Date(b[index].props.value) - new Date(a[index].props.value)
            } else {
            // string sort
            if (direction === 'asc') {
                return a[index].props.value.localeCompare(b[index].props.value);
            }
            return b[index].props.value.localeCompare(a[index].props.value);
            }
        });
        rows = updatedRows;
    };

    const onSortStatus = (event, index, direction) => {
        setActiveSortIndex(index);
        setActiveSortDirection(direction);
        // sorts the rows
        const updatedRows = rows.sort((a, b) => {
            // string sort
            if (direction === 'asc') {
                return a[index].props.children.localeCompare(b[index].props.children);
            }
            return b[index].props.children.localeCompare(a[index].props.children);
        });
        rows = updatedRows;
    };

    const getSortParams = (columnIndex, item) => ({
        sortBy: {
          index: activeSortIndex,
          direction: activeSortDirection
        },
        onSort: ((item === 'Status') ? onSortStatus : onSort),
        columnIndex
      });

    return <>
        {initialState && <><Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</>}
        {!initialState &&
        <Table  isStickyHeader={stickyHeader} {...props}>
          <Thead>
            <Tr>
                { columns && columns.map( (item, index) =>
                    <Th modifier="fitContent" key={index}
                        sort={getSortParams(index, item)}
                    >{item}</Th>)}
            </Tr>
          </Thead>
          <Tbody>
              { rows &&
                  rows.map( (item, index)=> <Tr key={index}>
                      {item.map( (value, idx) => <Td dataLabel={columns[idx]} key={idx}>{value}</Td> )}
                  </Tr> )
              }
          </Tbody>
        </Table>}
    </>
}
