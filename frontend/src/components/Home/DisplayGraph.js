import {PlotlyView} from "../ReactGraphs/plotly/PlotlyView";
import React, {useEffect} from "react";
import {useDispatch, useSelector} from "react-redux";
import CardView from "../PatternflyComponents/Card/CardView";
import {Text6} from "../PatternflyComponents/Text/Text";
import {SplitView} from "../PatternflyComponents/Split/SplitView";
import {Spinner} from "@patternfly/react-core";
import {fetchGraphData} from "../../store/Actions/ActionCreator";


export const DisplayGraph = ({uuid, benchmark}) => {

    const [isExpanded, setExpanded] = React.useState(true)
    const onExpand = () => setExpanded(!isExpanded)

    const dispatch = useDispatch()
    const job_results = useSelector(state => state.graph)
    const graphData = job_results.uuid_results[uuid]

    useEffect(() => {
            dispatch(fetchGraphData(uuid))
    }, [dispatch, uuid])

    const getGraphBody = () => {
        return (job_results.graphError && <Text6 value={job_results.graphError}/>) ||
               (graphData && <PlotlyView data={graphData} />) ||
               <SplitView splitValues={[<Spinner issvg={"true"} />, <Text6 value="Awaiting Results"/>]} />
    }

    return <>
            <CardView header={(benchmark && benchmark) || <Text6 value={"Graph Result"} />}
                      body={ getGraphBody() }
                      isExpanded={isExpanded}
                      expandView={true}
                      onExpand={onExpand}
            />
        </>
}
