import React, { useState, useEffect } from 'react';

export default function usePerfData() {
    const [perfData, setPerfData ] = useState([]);
    const query = {
        "query": {
            "range": {
                "timestamp": {
                    "gte": "now-1M",
                    "lte": "now",
                    "format": "strict_date_optional_time"
                }
            }
        }
    }
    const fetchPerfData = async () => {
        const requestOptions = {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
            // body: JSON.stringify(query)
        }
        var hostname = window.location.hostname
        var endpoint = "airflow"
        if (hostname == "localhost") {
            var host = "http://localhost:8000/api/v1/"+endpoint;
        } else {
            var host = window.location.protocol + '//' + window.location.hostname + "/api/v1/"+endpoint;
        }
        const response = await fetch(host, requestOptions)
        const perfData = await response.json()
        setPerfData(perfData.response)
    }

    useEffect(() => {
        fetchPerfData()
    }, [])

    return perfData
}