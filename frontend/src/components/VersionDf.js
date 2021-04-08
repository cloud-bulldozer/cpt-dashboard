import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import { TableComposable, TableHeader, TableText, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';

{/* <TableText
// modifier="fitContent"
// width={cellIndex < 2 ? colwidths[cellIndex] : 15}
>
{cell}
</TableText> */}

const VersionDf = (props) => {

  const colwidths = [25, 35]

  const columns = props.columns;

  const rows = props.data;

  const Colors = {
    'success': '#00800052',
    'warning': '#ffff00a1',
    'failed': '#ff000070',
    'upstream_failed': '#ffff00a1',
    'failure': '#ff000070',
    'N/A': '#00000000'
  }

  return (
    <>
      <Title headingLevel="h1" size={TitleSizes['xl']} id={props.version}>
        {props.version}
      </Title>
      <TableComposable
        aria-label="Simple table"
        variant='default'
        borders='compactBorderless'
      >
        <Thead>
          <Tr>
            {columns.map((column, columnIndex) => (
              <Th
                key={columnIndex}
                width={columnIndex < 2 ? 20 : 10}
                modifier="fitContent"
              >
                {column}
              </Th>
            ))}
          </Tr>
        </Thead>
        {rows.map((row, rowIndex) => {
          return (
            <Tbody key={rowIndex}>
              <>
                <Tr>
                  {row.map((cell, cellIndex) => {
                    var table_text = cell
                    var cell_text = cell
                    if (cell instanceof Array) {
                      cell_text = cell[0]
                      var cell_href = cell[1]
                      table_text = <a href={cell_href}>{cell_text}</a>
                    }
                    return (
                      <Td
                        key={`${rowIndex}_${cellIndex}`}
                        dataLabel={columns[cellIndex]}
                        component={cellIndex === 0 ? 'th' : 'td'}
                        style={{
                          backgroundColor: Colors[cell_text],
                          border: "1 px solid black"
                        }}
                      >
                        <TableText>
                      {table_text}
                    </TableText>
                      </Td>
                    );
                  })}
                </Tr>
              </>
            </Tbody>
          );
        })}
      </TableComposable>
    </>
  );
};

export default VersionDf