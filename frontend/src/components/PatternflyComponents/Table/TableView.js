
import {Table, Thead, Tr, Th, Tbody, Td, ExpandableRowContent} from '@patternfly/react-table';
import {Puff} from "react-loading-icons";
import React, {useEffect, useState} from "react";
import {BenchmarkResults} from "../../OCP/BenchmarkResults";


export const TableView = ({columns , rows = [], initialState = true, stickyHeader=false,
                              addExpandableRows = false, expandableComponent: ExpandableComponent,  ...props  }) => {
    /*
        rows: {
        dataset: {} // Complete data object
        tableRows: {} // Table values that need to be displayed
        }
    */


    const [expand, setExpand] = useState(
        Object.assign({}, ...Object.keys(rows).map( (items, idx) => ({[idx]: false})))
    )

    useEffect(()=>{
        if(rows)
        setExpand(
            Object.assign({}, ...Object.keys(rows).map( (items, idx) => ({[idx]: false})))
        )
    }, [rows])
    //
    const handleToggle = (event, index) => {
        setExpand({
            ...expand, [index]: !expand[index]
        })
    }


    const NonExpandableTableRows = () => {
        return <Tbody>
                    { rows &&
                      rows.map( (item, index)=> <Tr key={index}>
                          {item.tableRows.map( (value, idx) => <Td dataLabel={columns[idx]} key={idx}>{value}</Td> )}
                          </Tr>
                      )
                    }
               </Tbody>
    }

    const ExpandableRows = () => {
        return(
            <>
                { rows && rows.map( (item, index)=> <Tbody key={index} isExpanded={expand[index]}>
                        <Tr key={index}>
                               <Td expand={{
                                  rowIndex: index,
                                  isExpanded: expand[index],
                                  onToggle: handleToggle
                              }} />
                              {item.tableRows.map( (value, idx) => <Td dataLabel={columns[idx]} key={idx}>{value}</Td> )}
                        </Tr>
                        <Tr isExpanded={expand[index]}>
                              <Td dataLabel={columns[index]} noPadding colSpan={columns.length + 1}>
                                <ExpandableRowContent>
                                    { ExpandableComponent  &&
                                        <ExpandableComponent isExpanded={expand[index]} dataset={item.dataset}/>
                                    }
                                </ExpandableRowContent>
                              </Td>
                          </Tr>
                    </Tbody>)
                }
            </>
        )
    }

    // index of the currently active column
    const [activeSortIndex, setActiveSortIndex] = React.useState(-1);
    // sort direction of the currently active column
    const [activeSortDirection, setActiveSortDirection] = React.useState('none');

    const onSort = (event, index, direction) => {
        setActiveSortIndex(index);
        setActiveSortDirection(direction);
        // sorts the rows
        rows = rows.sort((a, b) => {
            a = a.tableRows
            b = b.tableRows
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
    };

    const onSortStatus = (event, index, direction) => {
        setActiveSortIndex(index);
        setActiveSortDirection(direction);
        // sorts the rows
        rows = rows.sort((a, b) => {
            a = a.tableRows
            b = b.tableRows
            // string sort
            if (direction === 'asc') {
                return a[index].props.children.localeCompare(b[index].props.children);
            }
            return b[index].props.children.localeCompare(a[index].props.children);
        });
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
                {addExpandableRows && <Th />}
                { columns && columns.map( (item, index) =>
                    <Th modifier="fitContent" key={index}
                        sort={getSortParams(index, item)}
                    >{item}</Th>)}
            </Tr>
          </Thead>
            {
                (addExpandableRows && ExpandableRows()) || NonExpandableTableRows()
            }
        </Table>}
    </>
}
