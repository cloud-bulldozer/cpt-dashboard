import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import { DisplayGrafana } from "./DisplayGrafana";


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
        <Card isExpanded={isExpanded}>
            <CardHeader
          onExpand={onExpand}
          toggleButtonProps={{
            id: 'toggle-button',
            'aria-label': 'Details',
            'aria-labelledby': 'titleId toggle-button',
            'aria-expanded': isExpanded
          }}
        >
                <CardTitle>Configs</CardTitle>

            </CardHeader>
            <CardExpandableContent>
            <CardBody>
                <Grid>
                    <GridItem rowSpan="1">
                        <Card><CardHeader><CardTitle>Cluster Metadata</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><span class="list-item-key">Release Binary</span>: {config.cluster_version  && config.cluster_version || config.ocpVersion}</li>
                                <li><span class="list-item-key">Cluster Name</span>: {config.cluster_name && config.cluster_name || config.clusterName}</li>
                                <li><span class="list-item-key">Cluster Type</span>: {config.cluster_type  && config.cluster_type || config.clusterType}</li>
                                <li><span class="list-item-key">Network Type</span>: {config.network_type  && config.network_type || config.networkType}</li>
                                <li><span class="list-item-key">Benchmark Status</span>: {icons[config.job_status  && config.job_status || config.jobStatus] || config.job_status  && config.job_status || config.jobStatus}</li>
                                <li><span class="list-item-key">Duration</span>: {formatTime(config.job_duration  && config.job_duration || config.jobDuration)}</li>
                                <li><span class="list-item-key">Test ID</span>: {config.uuid}</li>
                            </ul>

                            </CardBody></Card></GridItem>
                    <DisplayGrafana benchmarkConfigs={ config } />
                    <GridItem span="6">
                        <Card><CardHeader><CardTitle>Node Types</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><span class="list-item-key">Master</span>: {config.master_type  && config.master_type || config.masterNodesType}</li>
                                <li><span class="list-item-key">Worker</span>: {config.worker_type  && config.worker_type || config.workerNodesType}</li>
                                <li><span class="list-item-key">Workload</span>: {config.workload_type && config.workload_type || config.benchmark}</li>
                                <li><span class="list-item-key">Infra</span>: {config.infra_type  && config.infra_type || config.infraNodesType}</li>
                            </ul>
                            </CardBody></Card></GridItem><GridItem span="6">
                        <Card><CardHeader><CardTitle>Node Counts</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><span class="list-item-key">Master</span>: {config.master_count  && config.master_count || config.masterNodesCount}</li>
                                <li><span class="list-item-key">Worker</span>: {config.worker_count  && config.worker_count || config.workerNodesCount}</li>
                                <li><span class="list-item-key">Infra</span>: {config.infra_count  && config.infra_count || config.infraNodesCount}</li>
                                <li><span class="list-item-key">Total Nodes</span>: {config.workload_count  && config.workload_count || config.totalNodesCount}</li>
                            </ul>
                            </CardBody></Card>
                    </GridItem>
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
