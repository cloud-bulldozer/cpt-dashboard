import json
from fastapi import Response
from datetime import datetime, timedelta
from fastapi import APIRouter
from ..commons.common import getData

router = APIRouter()


@router.get('/api/v2/jobs')
async def jobsv2(start_date: datetime = None, end_date: datetime = None, pretty: bool = False):
    if start_date is None:
        start_date = datetime.utcnow()
        start_date = start_date - timedelta(days=5)

    if end_date is None:
        end_date = datetime.utcnow()

    if start_date > end_date:
        return Response(content="invalid date format, start_date must be less than end_date", status_code=422)

    response = await getData(start_date, end_date)

    if pretty:
        json_str = response.to_json(orient="records", indent=4)
        return Response(content=json_str, media_type='application/json')

    jsonstring = json.loads(response.to_json(orient="records"))
    return jsonstring
