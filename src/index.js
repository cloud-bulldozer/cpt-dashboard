import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import reportWebVitals from './reportWebVitals';

// import { Button } from '@patternfly/react-core';
import "@patternfly/react-core/dist/styles/base.css";
import './fonts.css';

// import BasicTable from './FilterableVersionTable';
import { ocpdata } from './mocks';

import { TableComposable, TableHeader, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';
import { Title, TitleSizes } from '@patternfly/react-core';
// import { ToggleGroup, ToggleGroupItem } from '@patternfly/react-core';

import { JumpLinks, JumpLinksItem } from '@patternfly/react-core';

const VersionTable = (props) => {
  const columns = [
    'Cloud Pipeline', 'Build Date', 'Run Date',
    'Build', 'Install', 'Uperf', 'HTTP', 'Kubelet', 'Object Density',
    'Upgrade'];
  const rows = props.data;
  return (
    <>
      <Title headingLevel="h2" size={TitleSizes['3xl']}>
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
    </>
  );
};

const VersionList = (props) => (
  props.data.map((t) => (
      <VersionTable 
        key={t.version}
        version={t.version}
        data={t.cloud_data} />
  ))
)

const WithLabels = (props) => (
  <>
    <JumpLinks label="jump to version links do not work">
      {props.data.map((t) => (
        <JumpLinksItem key={t.version}>
          {t.version}
        </JumpLinksItem>
      ))}
    </JumpLinks>
  </>
)

const VersionsDataframe = (props) => {
  const versions = props.data
  return (
    <>
    <Title headingLevel="h1" size={TitleSizes['4xl']}>
      OCP Performance at Scale
    </Title>
    <WithLabels data={versions} />
    <VersionList data={versions} />
    </>
  )
}



ReactDOM.render(
  <React.StrictMode>
    {/* <VersionList data={ocpdata} /> */}
    <VersionsDataframe data={ocpdata} />
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals();
