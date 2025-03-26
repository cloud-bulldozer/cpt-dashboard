import "./index.less";

import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
} from "@patternfly/react-icons";
import { Table, Tbody, Th, Thead, Tr } from "@patternfly/react-table";

import PropTypes from "prop-types";
import { Title } from "@patternfly/react-core";
import { formatTime } from "@/helpers/Formatters.js";
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
  const defaultValue = useMemo(() => {
    return {
      clusterType: "SNO spoke",
      networkType: "OVNKubernetes",
      masterNodesCount: "1",
      master_type: "Baremetal",
      totalNodesCount: "1",
    };
  }, []);
  const icons = useMemo(
    () => ({
      failed: <ExclamationCircleIcon fill={"#C9190B"} />,
      failure: <ExclamationCircleIcon fill={"#C9190B"} />,
      success: <CheckCircleIcon fill={"#3E8635"} />,
      upstream_failed: <ExclamationTriangleIcon fill={"#F0AB00"} />,
    }),
    []
  );
  return (
    <>
      <Title headingLevel="h4" className="type_heading">
        {props.heading}
      </Title>
      <Table className="box" key={uid()} aria-label="metadata-table" ouiaId="metadata-table">
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
              <Th>
                {item.value === "jobDuration"
                  ? formatTime(props.metadata[item.value])
                  : item.value === "jobStatus"
                  ? icons[props.metadata[item.value]]
                  : props.metadata[item.value] ?? defaultValue[item.value]}
              </Th>
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
