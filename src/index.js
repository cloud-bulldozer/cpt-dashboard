import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import reportWebVitals from './reportWebVitals';

// import { Button } from '@patternfly/react-core';
import "@patternfly/react-core/dist/styles/base.css";
import './fonts.css';

// import BasicTable from './FilterableVersionTable';
import { data } from './mocks';

import { TableComposable, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';
// import { ToggleGroup, ToggleGroupItem } from '@patternfly/react-core';

const FilterableVersionTable = (props) => {
  const columns = [
    'OCP Version', 'Cloud Pipeline', 'Build Date', 'Run Date',
    'Build', 'Install', 'Uperf', 'HTTP', 'Kubelet', 'Object Density',
    'Upgrade'];
  const rows = props.data;
  // const columns = ['Repositories', 'Branches', 'Pull requests', 'Workspaces', 'Last commit'];
  // const rows = [
  //   ['one', 'two', 'three', 'four', 'five'],
  //   ['one - 2', null, null, 'four - 2', 'five - 2'],
  //   ['one - 3', 'two - 3', 'three - 3', 'four - 3', {res:'five - 3', col:'yellow'}]
  // ];

  return (
    <React.Fragment>
      <TableComposable
        aria-label="Simple table"
        variant='compact'
        borders='compactBorderless'
      >
        <Caption>Simple table using composable components</Caption>
        <Thead>
          <Tr>
            {columns.map((column, columnIndex) => (
              <Th key={columnIndex}>{column}</Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {rows.map((row, rowIndex) => (
            <Tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <Td key={`${rowIndex}_${cellIndex}`} dataLabel={columns[cellIndex]}>
                  {cell}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </TableComposable>
    </React.Fragment>
  );
};



ReactDOM.render(
  <React.StrictMode>
    <FilterableVersionTable data={data}/> 
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals();
