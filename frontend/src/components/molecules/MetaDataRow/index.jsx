import "./index.less";

import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import { uid } from "@/utils/helper.js";

const MetadataRow = (props) => {
  const columnNames = {
    key: "Metadata",
    value: "Value",
  };
  return (
    <Table className="box" key={uid()} aria-label="metadata-table">
      <Thead>
        <Tr>
          <Th width={25} style={{ textAlign: "left" }}>
            {columnNames.key}
          </Th>
          <Th width={40}>{columnNames.value}</Th>
        </Tr>
      </Thead>
      <Tbody>
        {Object.entries(props.item).map((obj) => (
          <Tr key={uid()}>
            <Th>{obj[0]}</Th>
            <Th>{obj[1]}</Th>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default MetadataRow;
