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
                    <CardTitle>Tests Ran</CardTitle>
                </CardHeader>
                <CardExpandableContent>
                    <CardBody>
                        <ul>
                            {benchConfigs.map((benchConfig, index) => {
                                return (
                                    <>

                                        <li> {icons[benchConfig.job_status] || benchConfig.job_status}
                                            {benchConfig.build_tag} ({benchConfig.job_status != "upstream_failed" ? formatTime(benchConfig.job_duration) : "Skipped"})  <a href={benchConfig.build_url}><SiApacheairflow color="teal" /></a>
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
                <CardTitle>Tests Ran</CardTitle>
                <CardBody><Spinner isSVG /><br />Awaiting Results</CardBody>
                <CardFooter></CardFooter>
            </Card>
        )
    }

}