import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import { SiApacheairflow } from "react-icons/si";

export default function UpgradeCard(props) {
    let upgradeConfig = props.data

    const [isExpanded, setExpanded] = React.useState([false, false])

    const icons = {
        "failed": <><FaExclamationCircle color="red"/></>,
        "success": <><FaCheck color="green"/></>,
        "upstream_failed": <><FaExclamationTriangle color="yellow"/> Upstream Failed </>,

    }

    const onExpand = () => {
        setExpanded(!isExpanded)
      };


    if (upgradeConfig) {
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
                    <CardTitle>Upgrades</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                <CardBody>
                <ul>
                    <li> {icons[upgradeConfig.job_status] || upgradeConfig.job_status}
                     { upgradeConfig.job_status == "success" ? upgradeConfig.cluster_version : ""} ({upgradeConfig.job_status != "upstream_failed" ? formatTime(upgradeConfig.job_duration) : "Skipped" })</li>    
                     <a href={upgradeConfig.build_url}><SiApacheairflow color="teal"/></a>

                </ul>
                </CardBody>
                </CardExpandableContent>
            </Card>)
    } else {
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
                    <CardTitle>Upgrades</CardTitle>
                </CardHeader>
                <CardTitle>Upgrades</CardTitle>
                <CardExpandableContent>
                <CardBody><br />No Upgrade Results</CardBody>
                </CardExpandableContent>
                <CardFooter></CardFooter>
            </Card>
        )
    }

}