import "./index.less";

import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import PropTypes from "prop-types";
import { Title } from "@patternfly/react-core";
import { uid } from "@/utils/helper.js";
import { useMemo } from "react";
import { useSelector } from "react-redux";

const MetadataRow = (props) => {
  const columnNames = {
    key: "Metadata",
    value: "Value",
  };

  const { clusterMetaData, nodeKeys, nodeCount } = useSelector(
    (state) => state[props.type]
  );

  const memoObj = useMemo(() => {
    return {
      CLUSTER: clusterMetaData,
      NODE_TYPE: nodeKeys,
      NODE_COUNT: nodeCount,
    };
  }, [clusterMetaData, nodeKeys, nodeCount]);

  return (
    <>
      <Title headingLevel="h4">{props.heading}</Title>
      <Table className="box" key={uid()} aria-label="metadata-table">
        <Thead>
          <Tr>
            <Th width={20} style={{ textAlign: "left" }}>
              {columnNames.key}
            </Th>
            <Th width={20}>{columnNames.value}</Th>
          </Tr>
        </Thead>
        <Tbody>
          {memoObj[props?.category].map((item) => (
            <Tr key={uid()}>
              <Th>{item.name}</Th>
              <Th>{props.metadata[item.value]}</Th>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </>
  );
};

export default MetadataRow;
MetadataRow.propTypes = {
  metadata: PropTypes.object,
  category: PropTypes.string,
  type: PropTypes.string,
  heading: PropTypes.string,
};
