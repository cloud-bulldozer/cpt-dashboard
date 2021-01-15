import './App.css';
import './fonts.css';
import "@patternfly/react-core/dist/styles/base.css";

// import components
import OcpPerformanceApp from './components/OcpPerformanceApp';

// import fake data
import { ocpdata, ocpdata2 } from './mocks';

import { useState, useEffect } from 'react';


//const fastjson = require('fastjson');


//!!! this part doesn't work yet !!!
function App() {
  const [appState, setAppState] = useState([]);

  const query = {
                  "query": {
                        "range": {
                        "timestamp": {
                            "format": "strict_date_optional_time",
                            "gte": "2020-10-02T03:48:15.261Z",
                            "lte": "2021-01-11T04:48:15.261Z"
                        }
                        }
                  }
                }

  useEffect(() => {
    const requestOptions = {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(query)
    }
    fetch('http://localhost:8000/api/download', requestOptions)
      .then(res => res.json())
      .then((d) => setAppState(d.data));
  })

  
  return (
    <div className="App">
      <OcpPerformanceApp data={ocpdata}/>
    </div>
  );
}

export default App;
