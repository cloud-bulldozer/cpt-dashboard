import { PlotlyView } from "../ReactGraphs/plotly/PlotlyView";
import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import CardView from "../PatternflyComponents/Card/CardView";
import { Text6 } from "../PatternflyComponents/Text/Text";
import { SplitView } from "../PatternflyComponents/Split/SplitView";
import { Spinner } from "@patternfly/react-core";
import { fetchTelcoGraphData } from "../../store/Actions/ActionCreator";

export const DisplayGraph = ({ uuid, encryptedData, benchmark, heading }) => {
    const [isExpanded, setExpanded] = useState(true);
    const onExpand = () => setExpanded(!isExpanded);

    const dispatch = useDispatch();
    const jobResults = useSelector(state => state.telcoGraph);

    useEffect(() => {
        dispatch(fetchTelcoGraphData(uuid, encryptedData));
    }, [dispatch, uuid, encryptedData]);

    const graphData = jobResults.uuid_results[uuid];

    const getGraphBody = (key = null) => {
        const benchmarkGraph = graphData && graphData[benchmark];
        const dataForKey = key === null ? benchmarkGraph : benchmarkGraph?.[key];

        return jobResults.graphError
            ? <Text6 value={jobResults.graphError} />
            : dataForKey
                ? <PlotlyView data={dataForKey} />
                : <SplitView splitValues={[<Spinner isSVG="true" />, <Text6 value="Awaiting Results" />]} />;
    };

    const renderCard = (key, customHeading) => (
        <CardView
            header={customHeading || heading || <Text6 value="Graph Result" />}
            body={getGraphBody(key)}
            isExpanded={isExpanded}
            expandView={true}
            onExpand={onExpand}
        />
    );

    return (
        <>
            {benchmark === 'oslat' || benchmark === 'cyclictest' ? (
                <>
                    {renderCard('number_of_nines', `${benchmark} number of nines results`)}
                    {renderCard('max_latency', `${benchmark} latency results`)}
                </>
            ) : benchmark === 'deployment' ? (
                <>
                    {renderCard('total_minutes', `${benchmark} timing results`)}
                    {renderCard('total_reboot_count', `${benchmark} reboot count results`)}
                </>
            ) : (
                renderCard(null, `${benchmark} results`)
            )}
        </>
    );
};
