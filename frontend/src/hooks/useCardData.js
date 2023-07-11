import { useState, useEffect, componentDidMount } from 'react';

export default function useCardData(row, isExpanded) {
    const [cardData, setCardData] = useState([]);
    const pipeline_id = row[0]
    const job_id = row[1]

    const fetchCardData = async () => {
        const requestOptions = {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        }
        var hostname = window.location.hostname
        if (hostname == "localhost") {
            var host = "http://localhost:8000/api/results/" + pipeline_id + "/" + job_id;
        } else {
            var host = window.location.protocol + '//' + window.location.hostname + "/api/results/" + pipeline_id + "/" + job_id;
        }
        const response = await fetch(host, requestOptions)
        const cardData = await response.json()
        setCardData(cardData)
    }

    useEffect(() => {
        if (isExpanded === true) {
            fetchCardData()
        }
    }, [isExpanded])
    return cardData
}