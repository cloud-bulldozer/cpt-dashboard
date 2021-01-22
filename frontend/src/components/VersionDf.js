import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import { TableComposable, TableHeader, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';

const VersionDf = (props) => {
  
  const columns = [
    'Platform', 'Build Date', 'Run Date', 'Job', 'Build ID', 
    'Build', 'Install', 'Uperf', 'HTTP', 'Kubelet', 
    'Object Density', 'Upgrade'];

  const rows = props.data;

  // const Colors = new Map([
  //   ['success', '#00800052'],
  //   ['warning', '#ffff00a1'],
  //   ['failure', '#ff000070'],
  //   ['N/A', '#00000000']
  // ]);

  const Colors = {
    'success': '#00800052',
    'warning': '#ffff00a1',
    'failure': '#ff000070',
    'N/A': '#00000000'
  }

  const customRender = (cell, index) => {
    // coupled to the position of each column
    if (index <= 4) {
      return cell
    }
    return (
      <div>
        <a href={cell.url}>
          {cell.title}
        </a>
      </div>
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
            <>
              <Tr>
                {row.map((cell, cellIndex) => {
                  return (
                    <Td
                      key={`${rowIndex}_${cellIndex}`}
                      dataLabel={columns[cellIndex]}
                      component={cellIndex === 0 ? 'th' : 'td'}
                      style={{backgroundColor:Colors[cell], 
                        border:"1 px solid black"}}
                    >
                      {cell}
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