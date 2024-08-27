import * as CONSTANTS from "@/assets/constants/grafanaConstants";

import GrafanaIcon from "@/assets/images/grafana-icon.png";
import LinkIcon from "@/components/atoms/LinkIcon";
import Proptypes from "prop-types";
import { useMemo } from "react";

const GrafanaLink = (props) => {
  const { config, startDate, endDate } = props;
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

  return (
    <LinkIcon
      link={grafanaLink}
      target={"_blank"}
      src={GrafanaIcon}
      altText={"grafana link"}
      height={30}
      width={30}
    />
  );
};

GrafanaLink.propTypes = {
  config: Proptypes.object,
  endDate: Proptypes.number,
  startDate: Proptypes.number,
};

export default GrafanaLink;
