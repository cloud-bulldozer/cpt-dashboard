import { useState, useEffect, componentDidMount } from 'react';

export default function useCardData(row, isExpanded) {
    const [cardData, setCardData] = useState([]);
    const ci = row[0]
    const job_id = row[1]

    const fetchCardData = async () => {
        const requestOptions = {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        }
        var hostname = window.location.hostname
        var url = ""
        if (hostname === "localhost") {
            url = "http://localhost:8000/api/results/" + ci + "/" + job_id;
        } else {
            url = window.location.protocol + '//' + window.location.hostname + "/api/results/" + ci + "/" + job_id;
        }
        const response = await fetch(url, requestOptions)
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