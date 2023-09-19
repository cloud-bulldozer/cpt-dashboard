import json
from fastapi import Response
from datetime import datetime, timedelta
from fastapi import APIRouter
from ..commons.common import getData

router = APIRouter()


@router.get('/api/v2/jobs')
async def jobsv2(startDate: datetime = None, endDate: datetime = None, pretty: bool = False):
    if startDate is None:
        startDate = datetime.utcnow()
        startDate = startDate - timedelta(days=5)

    if endDate is None:
        endDate = datetime.utcnow()

    if startDate > endDate:
        return Response(content="", status_code=422)

    response = await getData(startDate, endDate)

    if pretty:
        json_str = response.to_json(orient="records", indent=4)
        return Response(content=json_str, media_type='application/json')

    jsonstring = json.loads(response.to_json(orient="records"))
    return jsonstring
