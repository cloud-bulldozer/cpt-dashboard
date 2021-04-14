
import React, { useState, useEffect } from 'react';
import { Tabs, Tab, TabTitleText, TabContent, Checkbox } from '@patternfly/react-core';
import { Grid, GridItem } from '@patternfly/react-core';

import VersionLinks from './VersionLinks';
import PerformanceEntry from './PerformanceEntry';


class VersionTabs extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        activeTabKey: 0
      };
      // Toggle currently active tab
      this.handleTabClick = (event, tabIndex) => {
        this.setState({
          activeTabKey: tabIndex
        });
      };
    }
  
    render() {
      const { activeTabKey } = this.state;
      const data = this.props.data;
      


      return (
        <Tabs activeKey={activeTabKey} isSecondary isFilled isBox variant="light300" onSelect={this.handleTabClick}>
        {this.props.data.map((tab, index) => (     
          <Tab eventKey={index} title={<TabTitleText>{tab.version}</TabTitleText>}> 
          <TabContent>
            <PerformanceEntry 
	        key={tab.version}
	        version={tab.version}
	        data={tab.cloud_data}
					columns={tab.columns} />
            </TabContent>
            
           </Tab>
          

         ))
        }
        </Tabs>
      );
    }
  }
  export default VersionTabs;