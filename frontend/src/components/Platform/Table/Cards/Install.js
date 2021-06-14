import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import { SiApacheairflow } from "react-icons/si";


export default function InstallCard(props) {
    let installConfigs = props.data
    const [isExpanded, setExpanded] = React.useState([true, null])


    const onExpand = () => {
        setExpanded(!isExpanded)
      };

      const icons = {
        "failed": <><FaExclamationCircle color="red"/></>,
        "success": <><FaCheck color="green"/></>,
        "upstream_failed": <><FaExclamationTriangle color="yellow"/></>,

    }

    if (installConfigs) {
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
                                <li><u>Release Binary</u>: {installConfigs.cluster_version}</li>
                                <li><u>Cluster Name</u>: {installConfigs.cluster_name}</li>
                                <li><u>Network Type</u>: {installConfigs.network_type}</li>
                                <li><u>Install Status</u>: {icons[installConfigs.job_status] || installConfigs.job_status} <a href={installConfigs.build_url}><SiApacheairflow color="teal"/></a></li>
                                <li><u>Duration</u>: {formatTime(installConfigs.job_duration)}</li>
                            </ul>
                            
                            </CardBody></Card></GridItem>

                    <GridItem span="6">
                        <Card isHoverable><CardHeader><CardTitle>Node Types</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><u>Master</u>: {installConfigs.master_type}</li>
                                <li><u>Worker</u>: {installConfigs.worker_type}</li>
                                <li><u>Workload</u>: {installConfigs.workload_type}</li>
                                <li><u>Infra</u>: {installConfigs.infra_type}</li>
                            </ul>
                            </CardBody></Card></GridItem><GridItem span="6">
                        <Card isHoverable><CardHeader><CardTitle>Node Counts</CardTitle></CardHeader>
                            <CardBody><ul>
                                <li><u>Master</u>: {installConfigs.master_count}</li>
                                <li><u>Worker</u>: {installConfigs.worker_count}</li>
                                <li><u>Workload</u>: {installConfigs.workload_count}</li>
                                <li><u>Infra</u>: {installConfigs.infra_count}</li>
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