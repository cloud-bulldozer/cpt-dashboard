import {useSelector} from "react-redux";
import {TableView} from "../PatternflyComponents/Table/TableView";
import {Text6} from "../PatternflyComponents/Text/Text";
import {Badge, Page} from "@patternfly/react-core";
import React from "react";


export const DataDisplayView = () => {

    const job_results = useSelector(state => state.jobs)

    const getRows = () => {
        return job_results.data.map( items => job_results.tableData.map( value => {
            if(value.name === 'Status')
                if(items[value.value].toLowerCase() === 'success')
                    return <Badge style={{backgroundColor: '#008000'}} children={items[value.value]} />
                else if(items[value.value].toLowerCase() === 'failure')
                    return <Badge style={{backgroundColor: '#ff0000'}} children={items[value.value]}/>
                else
                    return <Badge style={{backgroundColor: '#FFEA6C'}} children={items[value.value]}/>
            return <Text6 value={items[value.value]}/>
        }))
    }
    const getColumnNames = () => job_results.tableData.map( value => value.name)

    return <Page>
                <TableView initialState={job_results.initialState}
                           columns={getColumnNames()}
                           rows={getRows()}
                           stickyHeader={true}
                />
            </Page>
}

