import './App.css';
import './fonts.css';
import "@patternfly/react-core/dist/styles/base.css";

// import components
import OcpPerformanceApp from './components/OcpPerformanceApp';

import { useState, useEffect } from 'react';

function App() {
  const [appState, setAppState] = useState([]);

  const query = {
                  "query": {
                        "range": {
                        "timestamp": {
                          "gte": "2021-01-15T05:15:04.120Z",
                          "lte": "2021-01-22T05:15:04.120Z",
                          "format": "strict_date_optional_time"
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
      .then((d) => setAppState(d.response));
  }, [])

  return (
    <div className="App">
      <OcpPerformanceApp data={appState}/>
    </div>
    
  );
}

export default App;
