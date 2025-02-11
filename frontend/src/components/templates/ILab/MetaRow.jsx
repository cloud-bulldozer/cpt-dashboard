import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import Proptypes from "prop-types";
import { Title } from "@patternfly/react-core";
import { uid } from "@/utils/helper";

const MetaRow = (props) => {
  const { metadata, heading } = props;
  return (
    <>
      <Title headingLevel="h4" className="type_heading">
        {heading}
      </Title>
      <Table className="box" key={uid()} aria-label="metadata-table">
        <Thead>
          <Tr>
            <Th width={20} style={{ textAlign: "left" }}>
              Key
            </Th>
            <Th width={20}>Value</Th>
          </Tr>
        </Thead>
        <Tbody>
          {metadata.map((item) => (
            <Tr key={uid()}>
              <Th>{item[0]}</Th>
              <Th>{item[1]}</Th>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </>
  );
};

MetaRow.propTypes = {
  heading: Proptypes.string,
  metadata: Proptypes.array,
};
export default MetaRow;
