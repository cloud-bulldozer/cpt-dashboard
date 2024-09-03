import * as CONSTANTS from "@/assets/constants/splunkConstants";

import LinkIcon from "@/components/atoms/LinkIcon";
import Proptypes from "prop-types";
import SplunkIcon from "@/assets/images/splunk-icon.png";
import { useMemo } from "react";

const CONSTANTSLink = (props) => {
  const { config, startDate, endDate } = props;
  const splunkLink = useMemo(() => {
    const url = `${CONSTANTS.SPLUNK_BASE_URL}${
      CONSTANTS.BENCHMARK_URL[config.benchmark]
    }`;

    const query = `form.global_time.earliest=${encodeURIComponent(
      new Date(startDate).toISOString()
    )}&form.global_time.latest=${encodeURIComponent(
      new Date(endDate).toISOString()
    )}&form.formal_tag=${encodeURIComponent(
      config.formal
    )}&form.ocp_version=${encodeURIComponent(
      config.shortVersion
    )}&&form.ocp_build=${encodeURIComponent(
      config.ocpVersion
    )}&form.node_name=${encodeURIComponent(config.nodeName)}&
        &form.general_statistics=${encodeURIComponent(config.shortVersion)}`;

    const kernelQuery = `form.dashboard_kernels=${encodeURIComponent(
      config.kernel
    )}`;

    const histogramQuery = `form.histogram=${encodeURIComponent(
      config.ocpVersion
    )}`;

    switch (config.benchmark) {
      case "cyclictest": {
        return `${url}?${query}&${CONSTANTS.OCP_VIEW_QUERY}&${kernelQuery}`;
      }
      case "cpu_util": {
        return `${url}?${query}&${CONSTANTS.CPU_UTIL_QUERY}&${kernelQuery}`;
      }
      case "deployment": {
        return `${url}?${query}`;
      }
      case "oslat": {
        return `${url}?${query}&${CONSTANTS.OCP_VIEW_QUERY}&${CONSTANTS.CHART_COMPARISON_QUERY}&${kernelQuery}`;
      }
      case "ptp": {
        return `${url}?${query}&${CONSTANTS.BUBBLE_CHART_LEGEND_QUERY}${CONSTANTS.PTP_LEGEND_VALUE}&${kernelQuery}`;
      }
      case "reboot": {
        return `${url}?${query}&${CONSTANTS.CHART_COMPARISON_QUERY}&${CONSTANTS.REBOOT_QUERY}&${kernelQuery}`;
      }
      case "rfc-2544": {
        return `${url}?${query}&${CONSTANTS.BUBBLE_CHART_LEGEND_QUERY}${CONSTANTS.RFC_LEGEND_VALUE}&${histogramQuery}&${kernelQuery}`;
      }
    }
  }, [
    config.benchmark,
    config.formal,
    config.kernel,
    config.nodeName,
    config.ocpVersion,
    config.shortVersion,
    endDate,
    startDate,
  ]);

  return (
    <LinkIcon
      link={splunkLink}
      target={"_blank"}
      src={SplunkIcon}
      altText={"splunk link"}
      height={30}
      width={30}
    />
  );
};

CONSTANTSLink.propTypes = {
  config: Proptypes.object,
  endDate: Proptypes.number,
  startDate: Proptypes.number,
};
export default CONSTANTSLink;
