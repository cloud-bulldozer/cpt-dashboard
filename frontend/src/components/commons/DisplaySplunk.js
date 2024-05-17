import React from 'react';
import { FaCheck, FaExclamationCircle, FaExclamationTriangle } from "react-icons/fa";
import {formatTime} from "../../helpers/Formatters";
import {SplitView} from "../PatternflyComponents/Split/SplitView";
import CardView from "../PatternflyComponents/Card/CardView";
import ListView from "../PatternflyComponents/List/ListView";
import {Text6} from "../PatternflyComponents/Text/Text";
import { getBuildLink } from './commons';


export function DisplaySplunk({benchmarkConfigs}) {



    const icons = {
        "failed": <FaExclamationCircle color="red" />,
        "failure": <FaExclamationCircle color="red" />,
        "success": <FaCheck color="green" />,
        "upstream_failed": <FaExclamationTriangle color="yellow" />,

    }

    const {  getSplunkLink, getTimeFormat, status } = getSplunkData(benchmarkConfigs)

    return (
        <CardView header={"Tasks Ran"}
                  body={ benchmarkConfigs && <ListView isPlain={true} list_view={
                                      [<SplitView splitValues={[
                                                icons[status] || status,
                                                benchmarkConfigs.benchmark,
                                                `( ${getTimeFormat} )`,
                                                getSplunkLink,
                                                getBuildLink(benchmarkConfigs)]}
                                      />]
                                  }
                  /> || <Text6 value={"No Results"} /> }
        />
    )

}

const getSplunkData = (benchmarkConfigs) => {
    const splunkURL = "https://rhcorporate.splunkcloud.com/en-GB/app/search/";
    let status = null;
    let getTimeFormat = null;
    let getSplunkLink = null;
    if(benchmarkConfigs){
        const startDate = new Date(benchmarkConfigs.startDate)
        const endDate = new Date(benchmarkConfigs.endDate)

        // Adding 10 more minutes for a buffer.
        endDate.setMinutes(endDate.getMinutes() + 10);

        let getSplunkURL = null;
        switch(benchmarkConfigs.benchmark) {
            case 'cyclictest':
                getSplunkURL = `${splunkURL}cyclictest_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.ocp_view=ocp_version&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}`;
                break;
            case 'cpu_util':
                getSplunkURL = `${splunkURL}cpu_util_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.high_cpu_treshhold=0.03&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}&form.selected_duration=*&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}`;
                break;
            case 'deployment':
                getSplunkURL = `${splunkURL}deployment_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.charts_comparison=ocp_version&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}`;
                break;
            case 'oslat':
                getSplunkURL = `${splunkURL}oslat_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.ocp_view=ocp_version&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}`;
                break;
            case 'ptp':
                getSplunkURL = `${splunkURL}ptp_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.bubble_chart_legend=ocp_build&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}`;
                break;
            case 'reboot':
                getSplunkURL = `${splunkURL}reboot_kpis?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.charts_comparison=ocp_version&form.reboot_type=soft_reboot&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}`;
                break;
            case 'rfc-2544':
                getSplunkURL = `${splunkURL}rfc2544_?form.global_time.earliest=${encodeURIComponent(startDate.toISOString())}&form.global_time.latest=${encodeURIComponent(endDate.toISOString())}&form.bubble_chart_legend=kernel&form.formal_tag=${encodeURIComponent(benchmarkConfigs.formal)}&form.ocp_version=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.ocp_build=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.node_name=${encodeURIComponent(benchmarkConfigs.nodeName)}&form.general_statistics=${encodeURIComponent(benchmarkConfigs.shortVersion)}&form.histogram=${encodeURIComponent(benchmarkConfigs.ocpVersion)}&form.dashboard_kernels=${encodeURIComponent(benchmarkConfigs.kernel)}`;
                break;
        }

        getTimeFormat =  status !== "upstream_failed" ?
                                      formatTime(benchmarkConfigs.job_duration  &&
                                                      benchmarkConfigs.job_duration || benchmarkConfigs.jobDuration)
                                      : "Skipped"
        getSplunkLink = <a href={getSplunkURL} target={"_blank"}>
                            <img src={"assets/images/splunk-icon.png"}
                                 alt={"Splunk Logo"} style={{width:'25px',height:'25px'}} />
                         </a>
    }
    return {
        getSplunkLink, getTimeFormat, status
    }
}
