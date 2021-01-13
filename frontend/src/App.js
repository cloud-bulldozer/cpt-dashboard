import './App.css';
import './fonts.css';
import "@patternfly/react-core/dist/styles/base.css";

// import components
import OcpPerformanceApp from './components/OcpPerformanceApp';

// import fake data
import { ocpdata, ocpdata2 } from './mocks';

import { useState, useEffect } from 'react';


const fastjson = require('fastjson');




function App() {
  const [appState, setAppState] = useState([]);

  

  useEffect(() => {
    fetch('/api/widened')
      .then(res => res.json())
      .then((d) => setAppState(d.data));
  })



  
  return (
    <div className="App">

      <OcpPerformanceApp data={appState}/>
    </div>
  );
}

export default App;
