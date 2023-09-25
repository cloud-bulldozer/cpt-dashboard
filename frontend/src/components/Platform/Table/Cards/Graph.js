import React from 'react';
import { Card, CardTitle, CardBody, CardFooter, CardHeader, CardExpandableContent } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';
import { Spinner } from '@patternfly/react-core';
import { formatTime } from '../../../../helpers/Formatters'
import { FaCheck, FaExclamationCircle,  FaExclamationTriangle } from "react-icons/fa";
import Plotly from 'react-plotly.js';


export default function GraphCard(props) {
    let result = props.data
    const [isExpanded, setExpanded] = React.useState([true, null])


    const onExpand = () => {
        setExpanded(!isExpanded)
    };

    const [data, setData] = React.useState(null)
    React.useEffect(() => {
        (async () => {
           const data = await getData(result.uuid);
           setData(data);
        })();
    }, []);

    if ( result.uuid ) {
        console.log(data)
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
            <CardTitle>{result.benchmark}</CardTitle>
            </CardHeader>
            <CardExpandableContent>
            <CardBody>
            <Grid>
               <Plotly data={data}
                 layout={{"width": 800, "height": 600}}
                 />
            </Grid>
            </CardBody></CardExpandableContent>
            </Card>)
        } else {
            return (
                <Card>
                <CardTitle>Graph Result</CardTitle>
                <CardBody><Spinner isSVG /><br />Awaiting Results</CardBody>
                <CardFooter></CardFooter>
              </Card>
            )
        }
    }

async function getData(uuid) {
    var endpoint = "graph"
    var hostname = window.location.hostname
    if (hostname == "localhost") {
        var url = "http://localhost:8000/api/v1/"+endpoint+"/"+uuid;
    } else {
        var url = window.location.protocol + '//' + window.location.hostname + "/api/"+endpoint+"/"+uuid;
    }
    const response = await fetch(url);
    const data = await response.json();
    console.log(data)
    return data
  }
  