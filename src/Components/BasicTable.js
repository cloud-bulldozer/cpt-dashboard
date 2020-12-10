

import React from 'react';
import { TableComposable, Thead, Tbody, Tr, Th, Td, Caption } from '@patternfly/react-table';
import { ToggleGroup, ToggleGroupItem } from '@patternfly/react-core';

const BasicTable = () => {
  const columns = ['Repositories', 'Branches', 'Pull requests', 'Workspaces', 'Last commit'];
  const rows = [
    ['one', 'two', 'three', 'four', 'five'],
    ['one - 2', null, null, 'four - 2', 'five - 2'],
    ['one - 3', 'two - 3', 'three - 3', 'four - 3', 'five - 3']
  ];
  const [choice, setChoice] = React.useState('default');
  const handleItemClick = (isSelected, event) => {
    const id = event.currentTarget.id;
    setChoice(id);
  };
  return (
    <React.Fragment>
      <ToggleGroup aria-label="Default with single selectable">
        <ToggleGroupItem
          text="Default"
          buttonId="default"
          isSelected={choice === 'default'}
          onChange={handleItemClick}
        />
        <ToggleGroupItem
          text="Compact"
          buttonId="compact"
          isSelected={choice === 'compact'}
          onChange={handleItemClick}
        />
        <ToggleGroupItem
          text="Compact borderless"
          buttonId="compactBorderless"
          isSelected={choice === 'compactBorderless'}
          onChange={handleItemClick}
        />
      </ToggleGroup>
      <TableComposable
        aria-label="Simple table"
        variant={choice !== 'default' ? 'compact' : null}
        borders={choice !== 'compactBorderless'}
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

export default FilterableVersionTable;