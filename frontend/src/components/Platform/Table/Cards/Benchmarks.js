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
                                var sdate = new Date(benchConfig.start_date != '' && benchConfig.start_date || benchConfig.startDate).valueOf()
                                var edate = new Date(benchConfig.end_date != '' && benchConfig.end_date || benchConfig.endDate).valueOf()
                                var status = benchConfig.job_status != '' && benchConfig.job_status || benchConfig.jobStatus
                                var buildTag = benchConfig.build_tag != '' && benchConfig.build_tag || benchConfig.buildTag
                                let gimg = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Grafana_icon.svg/351px-Grafana_icon.svg.png"
                                return (
                                    <>
                                        <li> {icons[status] || status}
                                            {benchConfig.benchmark}
                                            ({status != "upstream_failed" ? formatTime(benchConfig.job_duration != '' && benchConfig.job_duration || benchConfig.jobDuration) : "Skipped"})
                                            <a href={benchConfig.build_url != '' && benchConfig.build_url || benchConfig.buildUrl}>
                                                <SiApacheairflow color="teal" />
                                            </a>
                                            <a href={"https://grafana.rdu2.scalelab.redhat.com:3000/d/9qdKt3K4z/kube-burner-report-ocp-wrapper?orgId=1&from="+sdate+"&to="+edate+"&var-Datasource=AWS%20Pro%20-%20ripsaw-kube-burner&var-platform="+benchConfig.platform+"&var-workload="+buildTag+"&var-uuid="+benchConfig.uuid}>
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