import {
    Grid,
    GridItem
} from "@patternfly/react-core";
import React from "react";
import PuffLoad from "../../PatternflyComponents/Spinners/PuffLoad";
import {Text4} from "../../PatternflyComponents/Text/Text";
import CardView from "../../PatternflyComponents/Card/CardView";
import PropTypes from "prop-types";


export const TopLayout = ({topHeadersData  = []}) => {

    const displayText = (textValue, loading) => {
        const load = loading? <PuffLoad /> : ""
        const value = <span>{textValue} {load}</span>
        return  <Text4 style={{color:"black"}} value={ value } />
    }

    return <>
        <Grid hasGutter={true} span={2}>
            {
                topHeadersData && topHeadersData.map( (item, index) => {
                    return <GridItem key={index}
                                     children={<CardView initialState={false}
                                                         header={<Text4 value={item.title} />}
                                                         body={displayText(item.value, item.loading )} />}  />
                } )
            }
        </Grid>
    </>
}


TopLayout.propTypes = {
    topHeadersData: PropTypes.arrayOf(
        PropTypes.shape({
            loading: PropTypes.bool.isRequired,
            title: PropTypes.string.isRequired,
            value: PropTypes.bool.isRequired,
        })
    ).isRequired
}
