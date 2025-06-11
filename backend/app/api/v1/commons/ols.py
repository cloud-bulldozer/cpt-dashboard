from datetime import date

from app.api.v1.commons.constants import OLS_FIELD_CONSTANT_DICT
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService


async def getFilterData(
    start_datetime: date, end_datetime: date, filter: str, configpath: str
):

    es = ElasticService(configpath=configpath)

    aggregate = utils.buildAggregateQuery(OLS_FIELD_CONSTANT_DICT)
    refiner = ""
    if filter:
        refiner = utils.transform_filter(filter)

    response = await es.filterPost(start_datetime, end_datetime, aggregate, refiner)
    await es.close()

    return {
        "filterData": response.get("filterData", []),
        "summary": response.get("summary", {}),
        "total": response.get("total", 0),
    }
