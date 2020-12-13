import React from 'react';

import { Title, TitleSizes } from '@patternfly/react-core';

import { TableComposable, TableHeader, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';

const VersionDf = (props) => {
  
  const columns = [
    'Cloud Pipeline', 'Build Date', 'Run Date',
    'Build', 'Install', 'Uperf', 'HTTP', 'Kubelet', 'Object Density',
    'Upgrade'];

  const rows = props.data;

  const Colors = new Map([
    ['success', 'green'],
    ['warning', 'yellow'],
    ['failure', 'red']
  ]);

  const customRender = (cell, index) => {
    // coupled to the position of each column
    if (index <= 2) {
      return cell
    }
    return (
      <>
      <a href={cell.url} style={{backgroundColor:Colors.get(cell.title)}}>
        {cell.title}
      </a>
      </>
    )
  }

  return (
    <>
      <Title headingLevel="h2" size={TitleSizes['3xl']} id={props.version}>
        {props.version}
      </Title>
      <TableComposable
        aria-label="Simple table"
        variant='compact'
        borders='compactBorderless'
      >
      <Thead>
        <Tr>
          {columns.map((column, columnIndex) => (
            <Th key={columnIndex}>{column}</Th>
          ))}
        </Tr>
      </Thead>
      {rows.map((row, rowIndex) => {
        return (
          <Tbody key={rowIndex}>
            <React.Fragment>
              <Tr>
                {row.map((cell, cellIndex) => {
                  return (
                    <Td
                      key={`${rowIndex}_${cellIndex}`}
                      dataLabel={columns[cellIndex]}
                      component={cellIndex === 0 ? 'th' : 'td'}
                    >
                      {customRender(cell, cellIndex)}
                    </Td>
                  );
                })}
              </Tr>
            </React.Fragment>
          </Tbody>
        );
      })}      
      </TableComposable>
    </>
  );
};

export default VersionDf