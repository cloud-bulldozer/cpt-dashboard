

import React from 'react';
import { FaCheck, FaExclamationCircle, FaExclamationTriangle } from "react-icons/fa";
import {formatTime} from "../../helpers/Formatters";
import {SplitView} from "../PatternflyComponents/Split/SplitView";
import CardView from "../PatternflyComponents/Card/CardView";
import ListView from "../PatternflyComponents/List/ListView";
import {Text6} from "../PatternflyComponents/Text/Text";


export function DisplayGrafana({benchmarkConfigs}) {



    const icons = {
        "failed": <FaExclamationCircle color="red" />,
        "failure": <FaExclamationCircle color="red" />,
        "success": <FaCheck color="green" />,
        "upstream_failed": <FaExclamationTriangle color="yellow" />,

    }

    const {  getGrafanaLink, getTimeFormat, status } = getGrafanaData(benchmarkConfigs)

    return (
        <CardView header={"Tasks Ran"}
                  body={ benchmarkConfigs && <ListView isPlain={true} list_view={
                                      [<SplitView splitValues={[
                                                icons[status] || status,
                                                benchmarkConfigs.benchmark,
                                                `( ${getTimeFormat} )`,
                                                getGrafanaLink]}
                                      />]
                                  }
                  /> || <Text6 value={"No Results"} /> }
        />
    )

}

const getGrafanaData = (benchmarkConfigs) => {
    const grafanaURL = "https://grafana.rdu2.scalelab.redhat.com:3000/d/";
    const dashboardKubeBurner = "9qdKt3K4z/kube-burner-report-ocp-wrapper?orgId=1"
    const dashboardIngress = "nlAhmRyVk/ingress-perf?orgId=1&var-termination=edge&" +
                                    "var-termination=http&var-termination=passthrough&" +
                                    "var-termination=reencrypt&var-latency_metric=p99_lat_us" +
                                    "&var-compare_by=uuid.keyword"
    const dashboardNetPerf = "wINGhybVz/k8s-netperf?orgId=1&var-samples=3&var-service=All&" +
                                    "var-parallelism=All&var-profile=All&var-messageSize=All&" +
                                    "var-driver=netperf&var-hostNetwork=true&var-hostNetwork=false"
    let status = null;
    let getTimeFormat = null;
    let getGrafanaLink = null;
    if(benchmarkConfigs){
        const startDate = new Date((benchmarkConfigs.start_date  && benchmarkConfigs.start_date) || benchmarkConfigs.startDate).valueOf()
        const endDate = new Date((benchmarkConfigs.end_date  && benchmarkConfigs.end_date) || benchmarkConfigs.endDate).valueOf()
        status = benchmarkConfigs.job_status  && benchmarkConfigs.job_status || benchmarkConfigs.jobStatus

        let dashboardURL = dashboardKubeBurner
        let dataSource = "&var-Datasource=AWS+Pro+-+ripsaw-kube-burner"
        if (benchmarkConfigs.ciSystem === "PROW"){
            dataSource = "&var-Datasource=QE+kube-burner"
            if (benchmarkConfigs.benchmark === "k8s-netperf") {
                dataSource = "&var-datasource=QE+K8s+netperf"
                dashboardURL = dashboardNetPerf
            }
            if (benchmarkConfigs.benchmark === "ingress-perf") {
                dataSource = "&var-datasource=QE+Ingress-perf"
                dashboardURL = dashboardIngress
            }
        } else if(benchmarkConfigs.ci_system === "JENKINS") {
            if (benchmarkConfigs.benchmark === "k8s-netperf") {
                dataSource = "&var-datasource=k8s-netperf"
                dashboardURL = dashboardNetPerf
            }
            if (benchmarkConfigs.benchmark === "ingress-perf") {
                dataSource = "&var-datasource=AWS+Pro+-+Ingress+performance+-+nextgen"
                dashboardURL = dashboardIngress
            }
        }
        const getGrafanaUrl = grafanaURL+dashboardURL+
                                 "&from="+startDate+"&to="+endDate+
                                 dataSource+"&var-platform="+benchmarkConfigs.platform+
                                 "&var-uuid="+benchmarkConfigs.uuid
        getTimeFormat =  status !== "upstream_failed" ?
                                      formatTime(benchmarkConfigs.job_duration  &&
                                                      benchmarkConfigs.job_duration || benchmarkConfigs.jobDuration)
                                      : "Skipped"
        getGrafanaLink = <a href={getGrafanaUrl} target={"_blank"}>
                            <img src={"assets/images/grafana-icon.png"}
                                 alt={"Grafana Logo"} style={{width:'25px',height:'25px'}} />
                         </a>
    }
    return {
        getGrafanaLink, getTimeFormat, status
    }
}
