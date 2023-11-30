
import {Badge, Page} from "@patternfly/react-core";
import React from "react";
import {InnerScrollContainer} from "@patternfly/react-table";
import {TableView} from "../../PatternflyComponents/Table/TableView";
import {Text6} from "../../PatternflyComponents/Text/Text";


export const DisplayTableDataLayout = ({initialState, tableMetaData, tableData, addExpandableRows= false,
                                       expandableComponent}) => {

   const getRows = () => {
       console.log(tableData)
        return  tableData && tableData.map( items => {
            const tableRows = tableMetaData.map( metadata => {
                console.log(items[metadata.value])
                if(metadata.name === 'Status')
                    if(items[metadata.value].toLowerCase() === "success")
                        return <Badge style={{backgroundColor: '#008000'}} children={items[metadata.value]} />
                    else if(items[metadata.value].toLowerCase() === "failure")
                        return <Badge style={{backgroundColor: '#ff0000'}} children={items[metadata.value]}/>
                    else
                        return <Badge style={{backgroundColor: '#FFEA6C'}} children={items[metadata.value]}/>
                if(metadata.name === 'Build URL')
                    return <a href={items[metadata.value]} target={"_blank"}>Job
                            <img src="assets/images/fa-external-link-alt.svg"
                                style={{width:'17px',height:'17px', 'margin-inline-start':'5px'}} />
                            </a>
                return <Text6 value={items[metadata.value]}/>
            })
            return {dataset: items, tableRows}
        })
    }
   const tableColumns = tableMetaData.map(item => item.name)
   return <Page>
                <InnerScrollContainer  children={<TableView initialState={initialState}
                                                             columns={tableColumns}
                                                             rows={getRows()}
                                                             stickyHeader={true}
                                                             addExpandableRows={addExpandableRows}
                                                             expandableComponent={expandableComponent}
                                                 />}
                />
         </Page>
}
