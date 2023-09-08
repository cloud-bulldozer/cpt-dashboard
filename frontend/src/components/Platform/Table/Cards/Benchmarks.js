import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle, FaExclamationTriangle } from "react-icons/fa";
import { SiApacheairflow } from "react-icons/si";


export default function BenchmarkCard(props) {
    let benchConfigs = props.data

    const [isExpanded, setExpanded] = React.useState([true, null])


    const icons = {
        "failed": <><FaExclamationCircle color="red" /></>,
        "failure": <><FaExclamationCircle color="red" /></>,
        "success": <><FaCheck color="green" /></>,
        "upstream_failed": <><FaExclamationTriangle color="yellow" /></>,

    }

    const onExpand = () => {
        setExpanded(!isExpanded)
    };


    if (benchConfigs && benchConfigs.length > 0) {
        console.log(benchConfigs)
        return (
            <Card isHoverable isExpanded={isExpanded}>
                <CardHeader
                    onExpand={onExpand}
                    toggleButtonProps={{
                        id: 'toggle-button',
                        'aria-label': 'Details',
                        'aria-labelledby': 'titleId toggle-button',
                        'aria-expanded': isExpanded
                    }}
                >
                    <CardTitle>Tasks Ran</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    <CardBody>
                        <ul>
                            {benchConfigs.map((benchConfig, index) => {
                                var grafanaURL = "https://grafana.rdu2.scalelab.redhat.com:3000/d/"
                                var sdate = new Date(benchConfig.start_date != '' && benchConfig.start_date || benchConfig.startDate).valueOf()
                                var edate = new Date(benchConfig.end_date != '' && benchConfig.end_date || benchConfig.endDate).valueOf()
                                var status = benchConfig.job_status != '' && benchConfig.job_status || benchConfig.jobStatus
                                var buildTag = benchConfig.build_tag != '' && benchConfig.build_tag || benchConfig.buildTag

                                var dashboardKubeBurner = "9qdKt3K4z/kube-burner-report-ocp-wrapper?orgId=1"
                                var dashboardIngress = "nlAhmRyVk/ingress-perf?orgId=1&var-termination=edge&var-termination=http&var-termination=passthrough&var-termination=reencrypt&var-latency_metric=p99_lat_us&var-compare_by=uuid.keyword"
                                var dashboardNetPerf = "wINGhybVz/k8s-netperf?orgId=1&var-samples=3&var-service=All&var-parallelism=All&var-profile=All&var-messageSize=All&var-driver=netperf&var-hostNetwork=true&var-hostNetwork=false"

                                var dashboardURL = dashboardKubeBurner
                                var dataSource = "&var-Datasource=AWS+Pro+-+ripsaw-kube-burner"
                                if (benchConfig.ciSystem === "JENKINS" || benchConfig.ciSystem === "PROW"){
                                    dataSource = "&var-Datasource=QE+kube-burner"
                                    if (benchConfig.benchmark === "k8s-netperf") {
                                        dataSource = "&var-datasource=QE+K8s+netperf"
                                        dashboardURL = dashboardNetPerf
                                    }
                                    if (benchConfig.benchmark === "ingress-perf") {
                                        dataSource = "&var-datasource=QE+Ingress-perf"
                                        dashboardURL = dashboardIngress
                                    }
                                } else if(benchConfig.ci_system === "JENKINS") {
                                    if (benchConfig.benchmark === "k8s-netperf") {
                                        dataSource = "&var-datasource=k8s-netperf"
                                        dashboardURL = dashboardNetPerf
                                    }
                                    if (benchConfig.benchmark === "ingress-perf") {
                                        dataSource = "&var-datasource=AWS+Pro+-+Ingress+performance+-+nextgen"
                                        dashboardURL = dashboardIngress
                                    }
                                }

                                let gimg = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Grafana_icon.svg/351px-Grafana_icon.svg.png"
                                return (
                                    <>
                                        <li> {icons[status] || status}
                                            {benchConfig.benchmark}
                                            ({status != "upstream_failed" ? formatTime(benchConfig.job_duration != '' && benchConfig.job_duration || benchConfig.jobDuration) : "Skipped"})
                                            <a href={benchConfig.build_url != '' && benchConfig.build_url || benchConfig.buildUrl}>
                                                <SiApacheairflow color="teal" />
                                            </a>
                                            <a href={grafanaURL+dashboardURL+"&from="+sdate+"&to="+edate+dataSource+"&var-platform="+benchConfig.platform+"&var-uuid="+benchConfig.uuid}>
                                                <img src={gimg} style={{width:'25px',heigh:'25px'}} />
                                            </a>
                                        </li>
                                    </>
                                )
                            })}

                        </ul>
                    </CardBody>
                </CardExpandableContent>
            </Card>)
    } else {
        return (
            <Card>
                <CardTitle>Tasks Ran</CardTitle>
                <CardBody><br />No Results</CardBody>
                <CardFooter></CardFooter>
            </Card>
        )
    }

}