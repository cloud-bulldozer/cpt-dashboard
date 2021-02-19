import '../OcpPerformanceTable.css';
import '../fonts.css';
import "@patternfly/react-core/dist/styles/base.css";

// import components
import OcpPerformanceHeader from './OcpPerformanceHeader';

import React, { useState, useEffect } from 'react';

const OcpPerformanceTableContext = React.createContext({
    data: {}, fetchPerfData: () => {}
})

export default function OcpPerformanceTable() {
    const [perfData, setPerfData] = useState([]);
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
    const fetchPerfData = async () => {
        const requestOptions = {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(query)
        }
        var hostname = window.location.hostname
        if (hostname == "localhost"){
            var host = "http//localhost:8000/api/download";
        } else {
            var host = window.location.protocol + '//' + window.location.hostname + "/api/download";
        }
        const response = await fetch(host, requestOptions)
        const perfData = await response.json()
        setPerfData(perfData.response)
  }

  useEffect(() => {
    fetchPerfData()
  }, [])

  return (
    <OcpPerformanceTableContext.Provider value={{perfData, fetchPerfData}}>
    <div className="OcpPerformanceTable">
      <OcpPerformanceHeader data={perfData}/>
    </div>
    </OcpPerformanceTableContext.Provider>
    
  );
}

