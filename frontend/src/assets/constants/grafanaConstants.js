export const GRAFANA_BASE_URL =
  "https://grafana.rdu2.scalelab.redhat.com:3000/d/";
export const DASHBOARD_KUBE_BURNER =
  "D5E8c5XVz/kube-burner-report-mode?orgId=1";
export const DASHBOARD_INGRESS =
  "d6105ff8-bc26-4d64-951e-56da771b703d/ingress-perf?orgId=1&var-termination=edge&" +
  "var-termination=http&var-termination=passthrough&" +
  "var-termination=reencrypt&var-latency_metric=p99_lat_us" +
  "&var-compare_by=uuid.keyword";
export const DASHBOARD_NET_PERF =
  "wINGhybVz/k8s-netperf?orgId=1&var-samples=3&var-service=All&" +
  "var-parallelism=All&var-profile=All&var-messageSize=All&" +
  "var-driver=netperf&var-hostNetwork=true&var-hostNetwork=false";
export const DASHBOARD_QUAY =
  "7nkJIoXVk/quay-dashboard-v2?orgId=1&var-api_endpoints_datasource=Quay%20QE%20-%20quay-vegeta&" +
  "var-quay_push_pull_datasource=Quay%20QE%20-%20quay-push-pull";
export const DASHBOARD_OLS = "edrn4yn2nu134d/ols-load-test-results?orgId=1&var-Datasource=AWS%20OCP%20QE%20OLS%20Load%20Test%20Results";

export const PROW_DATASOURCE_NETPERF = "&var-datasource=QE+K8s+netperf";
export const PROW_DATASOURCE_INGRESS = "&var-datasource=QE+Ingress-perf";
export const JENKINS_DATASOURCE_NETPERF = "&var-datasource=k8s-netperf";
export const JENKINS_DATASOURCE_INGRESS = "&var-datasource=QE+Ingress-perf";
export const PROW_DATASOURCE = "&var-Datasource=QE+kube-burner";
export const DEFAULT_DATASOURCE =
  "&var-Datasource=AWS+Pro+-+ripsaw-kube-burner";
export const QUAY_LOAD_TEST = "quay-load-test";
export const OLS_LOAD_GENERATOR = "ols-load-generator";

export const ciSystemMap = {
  prow: {
    "k8s-netperf": {
      dataSource: PROW_DATASOURCE_NETPERF,
      dashboardURL: DASHBOARD_NET_PERF,
    },
    "ingress-perf": {
      dataSource: PROW_DATASOURCE_INGRESS,
      dashboardURL: DASHBOARD_INGRESS,
    },
  },
  jenkins: {
    "k8s-netperf": {
      dataSource: JENKINS_DATASOURCE_NETPERF,
      dashboardURL: DASHBOARD_NET_PERF,
    },
    "ingress-perf": {
      dataSource: JENKINS_DATASOURCE_INGRESS,
      dashboardURL: DASHBOARD_INGRESS,
    },
  },
};
