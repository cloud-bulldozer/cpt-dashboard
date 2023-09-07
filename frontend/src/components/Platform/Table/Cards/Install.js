import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import { SiApacheairflow } from "react-icons/si";


export default function InstallCard(props) {
    let config = props.data
    const [isExpanded, setExpanded] = React.useState([true, null])


    const onExpand = () => {
        setExpanded(!isExpanded)
      };

      const icons = {
        "failed": <><FaExclamationCircle color="red"/></>,
        "success": <><FaCheck color="green"/></>,
        "upstream_failed": <><FaExclamationTriangle color="yellow"/></>,

    }

    if (config) {
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
                <CardTitle>Install Configs</CardTitle>

            </CardHeader>
            <CardExpandableContent>
            <CardBody>
                <Grid>
                    <GridItem rowSpan="1">
                        <Card isHoverable><CardHeader><CardTitle>Cluster Metadata</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><u>Release Binary</u>: {config.cluster_version != '' && config.cluster_version || config.ocpVersion}</li>
                                <li><u>Cluster Name</u>: {config.cluster_name != '' && config.cluster_name || config.clusterName}</li>
                                <li><u>Network Type</u>: {config.network_type != '' && config.network_type || config.networkType}</li>
                                <li><u>Install Status</u>: {icons[config.job_status != '' && config.job_status || config.jobStatus] || config.job_status != '' && config.job_status || config.jobStatus} <a href={config.build_url != '' && config.build_url || config.buildUrl}><SiApacheairflow color="teal"/></a></li>
                                <li><u>Duration</u>: {formatTime(config.job_duration != '' && config.job_duration || config.jobDuration)}</li>
                            </ul>

                            </CardBody></Card></GridItem>

                    <GridItem span="6">
                        <Card isHoverable><CardHeader><CardTitle>Node Types</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><u>Master</u>: {config.master_type != '' && config.master_type || config.masterNodesType}</li>
                                <li><u>Worker</u>: {config.worker_type != '' && config.worker_type || config.workerNodesType}</li>
                                <li><u>Workload</u>: {config.workload_type != '' && config.workload_type || config.benchmark}</li>
                                <li><u>Infra</u>: {config.infra_type != '' && config.infra_type || config.infraNodesType}</li>
                            </ul>
                            </CardBody></Card></GridItem><GridItem span="6">
                        <Card isHoverable><CardHeader><CardTitle>Node Counts</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><u>Master</u>: {config.master_count != '' && config.master_count || config.masterNodesCount}</li>
                                <li><u>Worker</u>: {config.worker_count != '' && config.worker_count || config.workerNodesCount}</li>
                                <li><u>Infra</u>: {config.infra_count != '' && config.infra_count || config.infraNodesCount}</li>
                                <li><u>Total Nodes</u>: {config.workload_count != '' && config.workload_count || config.totalNodesCount}</li>
                            </ul>
                            </CardBody></Card></GridItem>
                </Grid>
            </CardBody></CardExpandableContent>


        </Card>)
    } else {
        return (
            <Card>
            <CardTitle>Install Configuration</CardTitle>
            <CardBody><Spinner isSVG /><br />Awaiting Results</CardBody>
            <CardFooter></CardFooter>
          </Card>
        )
    }

}
