import {PlotlyView} from "../ReactGraphs/plotly/PlotlyView";
import React, {useEffect} from "react";
import {useDispatch, useSelector} from "react-redux";
import CardView from "../PatternflyComponents/Card/CardView";
import {Text6} from "../PatternflyComponents/Text/Text";
import {SplitView} from "../PatternflyComponents/Split/SplitView";
import {Spinner} from "@patternfly/react-core";
import {fetchQuayGraphData} from "../../store/Actions/ActionCreator";


export const DisplayGraph = ({uuid, resultKey, heading}) => {

    const [isExpanded, setExpanded] = React.useState(true)
    const onExpand = () => setExpanded(!isExpanded)

    const dispatch = useDispatch()
    const job_results = useSelector(state => state.quayGraph)
    const graphData = job_results.uuid_results[uuid]
    console.log(graphData)

    useEffect(() => {
            dispatch(fetchQuayGraphData(uuid))
    }, [dispatch, uuid])

    const getGraphBody = () => {
        const dataForKey = graphData && graphData[resultKey];
        return (job_results.graphError && <Text6 value={job_results.graphError}/>) ||
               (dataForKey && <PlotlyView data={dataForKey} />) ||
               <SplitView splitValues={[<Spinner issvg={"true"} />, <Text6 value="Awaiting Results"/>]} />
    }

    return <>
            <CardView header={(heading && heading) || <Text6 value={"Graph Result"} />}
                      body={ getGraphBody() }
                      isExpanded={isExpanded}
                      expandView={true}
                      onExpand={onExpand}
            />
        </>
}
