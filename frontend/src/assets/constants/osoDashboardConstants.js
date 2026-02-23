/**
 * OSO (RHOSO) dashboard and artifact link templates.
 * Placeholders are replaced in OsoDashboardLink using row data.
 */

/** RHOSO Performance Dashboard (Grafana). Use row startDate/endDate as ms for {from}/{to}, buildId for {buildId}. */
export const RHOSO_PERFORMANCE_DASHBOARD_TEMPLATE =
  "https://grafana.app.intlab.redhat.com/d/7584fd37-1f5e-4ad6-a1ca-fb56586a660c/rhoso-performance-dashboard?orgId=2&from={from}&to={to}&var-Datasource=osp-metrics-from-ocp&var-Index=All&var-job_name=cpt-{buildId}&var-node=All";

/** Rally Compare Dashboard (Grafana). Use row uuid for {uuid}. */
export const RALLY_COMPARE_DASHBOARD_TEMPLATE =
  "https://grafana.app.intlab.redhat.com/d/V8QvcQmvz/rally-compare-dashboard?orgId=2&refresh=5s&from=now-90d&to=now&var-Datasource=browbeat-rally-*&var-uuid={uuid}&var-scenario=All&var-action=All";

/** Pub / artifacts. Use row buildId for {buildId} */
export const PUB_ARTIFACTS_TEMPLATE =
  "https://perf1.perf.eng.bos2.dc.redhat.com/pub/RHOSO_CPT/{buildId}/";
