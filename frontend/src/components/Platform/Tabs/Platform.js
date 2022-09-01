import ReactDOM from 'react-dom';
import React, { useState, useEffect } from 'react';
import { Tabs, Tab, TabTitleText, TabContent, TabTitleIcon, Checkbox } from '@patternfly/react-core';
import { FaAws, FaMicrosoft,  FaGoogle } from "react-icons/fa";

import VersionTabs from './Version';
import './Platform.css'

class PlatformTabs extends React.Component {
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
    const icons = {
         'azure': <><TabTitleIcon><FaMicrosoft /></TabTitleIcon><TabTitleText>Azure</TabTitleText></>,
         'gcp':  <><TabTitleIcon><FaGoogle /></TabTitleIcon><TabTitleText>GCP</TabTitleText></>,
         'aws': <><TabTitleIcon><FaAws /></TabTitleIcon><TabTitleText>AWS</TabTitleText></>
    }
    return (
      <Tabs activeKey={activeTabKey} onSelect={this.handleTabClick}>
      {this.props.data.map((tab, index) => (
        <Tab key={index} eventKey={index} title={(icons[tab.title] || <TabTitleText>{tab.title}</TabTitleText>)}>
          <TabContent>
          <VersionTabs data={tab.data} />
          </TabContent>
         </Tab>
       ))
      }
      </Tabs>
    );
  }
}
export default PlatformTabs;
