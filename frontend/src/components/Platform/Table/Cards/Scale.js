import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle, FaExclamationTriangle } from "react-icons/fa";
import { SiApacheairflow } from "react-icons/si";


export default function ScaleCard(props) {
    let scaleConfigs = props.data

    const [isExpanded, setExpanded] = React.useState([false, false])


    const onExpand = () => {
        setExpanded(!isExpanded)
    };

    const icons = {
        "failed": <><FaExclamationCircle color="red" /></>,
        "success": <><FaCheck color="green" /></>,
        "upstream_failed": <><FaExclamationTriangle color="yellow" /></>,

    }

    if (scaleConfigs && scaleConfigs.length > 0) {
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
                    <CardTitle>Scale Configs</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    <CardBody>
                        <ul>
                            {scaleConfigs.map((scaleConfig, index) => {
                                return (

                                    <li>{icons[scaleConfig.job_status] || scaleConfig.job_status} {scaleConfig.build_tag == "scale" ? "25" : scaleConfig.build_tag.split("scale_")} Workers 
                                    ({scaleConfig.job_status == "success" ? formatTime(scaleConfig.job_duration) : "Skipped"}) <a href={scaleConfig.build_url}><SiApacheairflow color="teal"/></a></li>


                                )
                            })}

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
                        'aria-expanded': false
                    }}
                >
                    <CardTitle>Scale Configs</CardTitle>
                </CardHeader>
                <CardTitle>Scale Configuration</CardTitle>
                <CardExpandableContent>
                <CardBody><br />No Scale Configuration</CardBody>
                </CardExpandableContent>
                <CardFooter></CardFooter>
            </Card>
        )
    }
}