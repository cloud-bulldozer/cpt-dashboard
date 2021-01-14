import React from 'react';
import { Title, TitleSizes } from '@patternfly/react-core';
import { TableComposable, TableHeader, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';

const VersionDf = (props) => {
  
  const columns = [
    'Platform', 'Build Date', 'Run Date', 'Job', 'Build ID', 
    'Build', 'Install', 'Uperf', 'HTTP', 'Kubelet', 
    'Object Density', 'Upgrade'];

  const rows = props.data;

  const Colors = new Map([
    ['success', '#00800052'],
    ['warning', '#ffff00a1'],
    ['failure', '#ff000070']
  ]);

  const customRender = (cell, index) => {
    if (cell instanceof Object) {
      if (cell.url) {
        return (
          <div>
            <a href={cell.url}>
              {cell.title}
            </a>
          </div>
        )
      }
      return cell.title
    }
    return cell
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
                      style={{backgroundColor:Colors.get(cell.title), 
                        border:"1 px solid black"}}
                    >
                      {customRender(cell, cellIndex)}
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