import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import { DisplaySplunk } from '../commons/DisplaySplunk';


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
                            <CardBody>
                            <ul>
                                <li><span class="list-item-key">Release Binary</span>: {config.cluster_version  && config.cluster_version || config.ocpVersion}</li>
                                <li><span class="list-item-key">Cluster Name</span>: {config.cluster_name && config.cluster_name || config.nodeName}</li>
                                <li><span class="list-item-key">Cluster Type</span>: {config.cluster_type  && config.cluster_type || "SNO spoke"}</li>
                                <li><span class="list-item-key">Network Type</span>: {config.network_type  && config.network_type || "OVNKubernetes"}</li>
                                <li><span class="list-item-key">CPU</span>: {config.cpu_version  && config.cpu_version || config.cpu}</li>
                                <li><span class="list-item-key">Kernel</span>: {config.kernel_version  && config.kernel_version || config.kernel}</li>
                                <li><span class="list-item-key">IsFormal</span>: {config.is_formal  && config.is_formal || config.formal}</li>
                                <li><span class="list-item-key">Benchmark Status</span>: {icons[config.job_status  && config.job_status || config.jobStatus] || config.job_status  && config.job_status || config.jobStatus}</li>
                                <li><span class="list-item-key">Duration</span>: {formatTime(config.job_duration  && config.job_duration || config.jobDuration)}</li>
                            </ul>
                            </CardBody>
                        </Card>
                    </GridItem>
                    <DisplaySplunk benchmarkConfigs={ config } />
                    <GridItem span="6">
                        <Card><CardHeader><CardTitle>Node Types</CardTitle></CardHeader>
                            <CardBody>
                            <ul>
                                <li><span class="list-item-key">Master</span>: {config.master_type  && config.master_type || "Baremetal"}</li>
                                <li><span class="list-item-key">Workload</span>: {config.workload_type && config.workload_type || config.benchmark}</li>
                            </ul>
                            </CardBody>
                        </Card>
                    </GridItem>
                    <GridItem span="6">
                        <Card><CardHeader><CardTitle>Node Counts</CardTitle></CardHeader>
                            <CardBody>
                            <ul>
                                <li><span class="list-item-key">Master</span>: {config.master_count  && config.master_count || "1"}</li>
                                <li><span class="list-item-key">Total Nodes</span>: {config.workload_count  && config.workload_count || "1"}</li>
                            </ul>
                            </CardBody>
                        </Card>
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
