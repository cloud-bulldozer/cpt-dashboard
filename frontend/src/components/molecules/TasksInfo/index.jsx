import "./index.less";

import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
} from "@patternfly/react-icons";

import GrafanaLink from "@/components/atoms/GrafanaLink";
import JenkinsIcon from "@/assets/images/jenkins-icon.svg";
import LinkIcon from "@/components/atoms/LinkIcon";
import OsoDashboardLink from "@/components/atoms/osoDashboardLink";
import Proptypes from "prop-types";
import ProwIcon from "@/assets/images/prow-icon.png";
import SplunkLink from "@/components/atoms/SplunkLink";
import { formatTime } from "@/helpers/Formatters.js";
import { useMemo } from "react";

const TasksInfo = (props) => {
  const { config } = props;

  const startDate = useMemo(
    () => new Date(config?.startDate).valueOf(),
    [config?.startDate]
  );
  const endDate = useMemo(
    () => new Date(config?.endDate).valueOf() + 10 * 60 * 1000,
    [config?.endDate]
  );

  const status = useMemo(
    () => config.jobStatus?.toLowerCase(),
    [config.jobStatus]
  );

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
      <div className="info-wrapper">
        <div>{icons[status] ?? status.toUpperCase()}</div>
        <div>{config.benchmark}</div>
        <div>
          {status !== "upstream_failed"
            ? `(${formatTime(config?.jobDuration)})`
            : "Skipped"}
        </div>
        {(props.type === "ocp" || props.type === "quay" || props.type === "ols") && (
          <GrafanaLink
            config={config}
            startDate={startDate}
            endDate={endDate}
          />
        )}
        {props.type === "telco" && (
          <SplunkLink config={config} startDate={startDate} endDate={endDate} />
        )}
        {props.type === "oso" && (
          <OsoDashboardLink
            config={config}
            startDate={startDate - 10 * 60 * 1000}
            endDate={endDate - 5 * 60 * 1000}
          />
        )}
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
  type: Proptypes.string,
};
export default TasksInfo;
