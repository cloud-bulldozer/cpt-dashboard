import ReactDOM from 'react-dom';
// import "@patternfly/react-core/dist/styles/base.css";
// import './fonts.css';

import React, { useState, useEffect } from 'react';
import { Tabs, Tab, TabTitleText, Checkbox } from '@patternfly/react-core';

import WithLabels from './WithLabels';
import VersionList from './VersionList';


// export default function SimpleTabs(props) {
//   const [activeTabKey, setActiveKey] = useState([]);

//   return (
//     <Tabs activeKey={activeTabKey} onSelect={setActiveKey(index)}>
//       {props.data.map((tab, index) => (      
//         <Tab eventKey={index} title={<TabTitleText>tab.title</TabTitleText>}>
//           <WithLabels data={tab.versions} />
//           <VersionList data={tab.versions} />
//         </Tab>
//       ))}
//     </Tabs>
//   );
// }

class SimpleTabs extends React.Component {
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
      <div>
      <Tabs activeKey={activeTabKey} onSelect={this.handleTabClick}>
      {this.props.data.map((tab, index) => (         
        <Tab eventKey={index} title={<TabTitleText>{tab.title}</TabTitleText>}> 
          <WithLabels data={tab.data} />
          <VersionList data={tab.data} />
         </Tab>
       ))
      }
      </Tabs>
      </div>
    );
  }
}
export default SimpleTabs;