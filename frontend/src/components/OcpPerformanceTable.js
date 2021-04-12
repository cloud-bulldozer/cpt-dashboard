import '../OcpPerformanceTable.css';
import '../fonts.css';
import "@patternfly/react-core/dist/styles/base.css";
import SimpleTabs from './PerformanceTabs';

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
                          "gte": "now-3M",
                          "lte": "now",
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
            var host = "http://localhost:8000/api/results";
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
    <>
    <OcpPerformanceTableContext.Provider value={{perfData, fetchPerfData}}>
      <div className="OcpPerformanceTable-header">
      <OcpPerformanceHeader data={perfData}/>
    </div>
    <div className="OcpPerformanceTable">
      <SimpleTabs data={perfData} />
    </div>
    </OcpPerformanceTableContext.Provider>
    </>
  );
}

