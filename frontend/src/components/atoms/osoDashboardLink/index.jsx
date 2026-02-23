import * as CONSTANTS from "@/assets/constants/osoDashboardConstants";
import LinkIcon from "@/components/atoms/LinkIcon";
import Proptypes from "prop-types";
import { useMemo } from "react";

const OsoDashboardLink = (props) => {
  const { config, startDate, endDate } = props;

  const links = useMemo(() => {
    const from = startDate != null ? Number(startDate) : null;
    const to = endDate != null ? Number(endDate) : null;
    const uuid = config?.uuid?.trim?.() || "";
    const buildId = config?.buildId?.trim?.() || "";

    const link1 =
      from != null && to != null && buildId
        ? CONSTANTS.RHOSO_PERFORMANCE_DASHBOARD_TEMPLATE.replace(
            "{from}",
            String(from)
          )
          .replace("{to}", String(to))
          .replace("{buildId}", buildId)
        : null;

    const link2 = uuid
      ? CONSTANTS.RALLY_COMPARE_DASHBOARD_TEMPLATE.replace("{uuid}", uuid)
      : null;

    const link3 = buildId
      ? CONSTANTS.PUB_ARTIFACTS_TEMPLATE.replace("{buildId}", buildId)
      : null;

    return [
      { url: link1, altText: "Performance Dashboard" },
      { url: link2, altText: "Rally Dashboard" },
      { url: link3, altText: "Artifacts" },
    ];
  }, [config?.uuid, config?.buildId, startDate, endDate]);

  return (
    <>
      {links.map(
        (item, idx) =>
          item.url && (
            <span key={idx} style={{ marginRight: "0.5rem" }}>
              <LinkIcon
                link={item.url}
                target="_blank"
                altText={item.altText}
              />
            </span>
          )
      )}
    </>
  );
};

OsoDashboardLink.propTypes = {
  config: Proptypes.object,
  startDate: Proptypes.number,
  endDate: Proptypes.number,
};

export default OsoDashboardLink;
