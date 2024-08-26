import "./index.less";

import * as CONSTANTS from "@/assets/constants/grafanaConstants";

import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
} from "@patternfly/react-icons";

import GrafanaIcon from "@/assets/images/grafana-icon.png";
import JenkinsIcon from "@/assets/images/jenkins-icon.svg";
import LinkIcon from "@/components/atoms/LinkIcon";
import Proptypes from "prop-types";
import ProwIcon from "@/assets/images/prow-icon.png";
import { formatTime } from "@/helpers/Formatters.js";
import { useMemo } from "react";

const TasksInfo = (props) => {
  const { config } = props;

  const startDate = useMemo(
    () => new Date(config?.startDate).valueOf(),
    [config?.startDate]
  );
  const endDate = useMemo(
    () => new Date(config?.endDate).valueOf(),
    [config?.endDate]
  );

  const status = useMemo(
    () => config.jobStatus?.toLowerCase(),
    [config.jobStatus]
  );

  const grafanaLink = useMemo(() => {
    const ciSystem_lCase = config.ciSystem?.toLowerCase();
    const isProw = ciSystem_lCase === "prow";
    const discreteBenchmark =
      CONSTANTS.ciSystemMap[ciSystem_lCase]?.[ciSystem_lCase?.benchmark];

    const hasBenchmark = Object.prototype.hasOwnProperty.call(
      CONSTANTS.ciSystemMap?.[ciSystem_lCase],
      config.benchmark
    );
    const datasource = isProw
      ? CONSTANTS.PROW_DATASOURCE
      : hasBenchmark
      ? discreteBenchmark?.dataSource
      : CONSTANTS.DEFAULT_DATASOURCE;

    const dashboardURL =
      discreteBenchmark?.dashboardURL ?? CONSTANTS.DASHBOARD_KUBE_BURNER;

    const datePart = `&from=${startDate}&to=${endDate}`;
    const uuidPart = `&var-uuid=${config.uuid}`;

    if (config.benchmark === CONSTANTS.QUAY_LOAD_TEST)
      return `${CONSTANTS.GRAFANA_BASE_URL}${CONSTANTS.DASHBOARD_QUAY}${datePart}${uuidPart}`;
    return `${CONSTANTS.GRAFANA_BASE_URL}${dashboardURL}${datasource}${datePart}&var-platform=${config.platform}"&var-workload=${config.benchmark}${uuidPart}`;
  }, [
    config.benchmark,
    config.ciSystem,
    config.platform,
    config.uuid,
    endDate,
    startDate,
  ]);

  const icons = useMemo(
    () => ({
      failed: <ExclamationCircleIcon />,
      failure: <ExclamationCircleIcon />,
      success: <CheckCircleIcon />,
      upstream_failed: <ExclamationTriangleIcon />,
    }),
    []
  );
  return (
    <>
      <div className="info-wrapper">
        <div>{icons[status] ?? status.toUpperCase()}</div>
        <div>{config.benchmark}</div>
        <div>{`(${formatTime(config?.jobDuration)})`}</div>
        <LinkIcon
          link={grafanaLink}
          target={"_blank"}
          src={GrafanaIcon}
          altText={"grafana link"}
          height={30}
          width={30}
        />
        <LinkIcon
          link={config.buildUrl}
          target={"_blank"}
          src={config.ciSystem === "PROW" ? ProwIcon : JenkinsIcon}
          altText={"build link"}
          height={30}
          width={30}
        />
      </div>
    </>
  );
};
TasksInfo.propTypes = {
  config: Proptypes.object,
};
export default TasksInfo;
