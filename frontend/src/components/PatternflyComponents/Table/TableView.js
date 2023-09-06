
import {Table, Thead, Tr, Th, Tbody, Td} from '@patternfly/react-table';
import {Puff} from "react-loading-icons";
import React from "react";


export const TableView = ({columns , rows = [], initialState = true, stickyHeader=false, ...props  }) => {
    return <>
        {initialState && <><Puff stroke="#0000FF" strokeOpacity={.125} speed={.75} /> Loading....</>}
        {!initialState &&
        <Table  isStickyHeader={stickyHeader} {...props}>
          <Thead>
            <Tr>
                { columns && columns.map( (item, index) => <Th modifier="fitContent" key={index}>{item}</Th>)}
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
