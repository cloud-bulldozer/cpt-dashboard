export const SPLUNK_BASE_URL =
  "https://rhcorporate.splunkcloud.com/en-GB/app/search/";

export const BENCHMARK_URL = {
  cyclictest: "cyclictest_kpis",
  cpu_util: "cpu_util_kpis",
  deployment: "deployment_kpis",
  oslat: "oslat_kpis",
  ptp: "ptp_kpis",
  reboot: "reboot_kpis",
  "rfc-2544": "rfc2544_",
};

export const THRESHOLD_VALUE = 0.03;
export const CPU_UTIL_QUERY = `form.high_cpu_treshhold=${THRESHOLD_VALUE}&form.selected_duration=*`;
export const CHART_COMPARISON_QUERY = `form.charts_comparison=ocp_version`;
export const OCP_VIEW_QUERY = `form.ocp_view=ocp_version`;
export const REBOOT_QUERY = `form.reboot_type=soft_reboot`;

export const BUBBLE_CHART_LEGEND_QUERY = "form.bubble_chart_legend=";
export const RFC_LEGEND_VALUE = "kernel";
export const PTP_LEGEND_VALUE = "ocp_build";
