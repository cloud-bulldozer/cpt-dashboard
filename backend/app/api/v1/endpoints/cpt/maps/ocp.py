from app.api.v1.commons.ocp import getData, getFilterData
from app.api.v1.commons.utils import getReleaseStream
from datetime import date
import pandas as pd


################################################################
# This will return a DataFrame from OCP required by the CPT endpoint
################################################################
async def ocpMapper(
    start_datetime: date, end_datetime: date, size: int, offset: int, filter: str
):
    response = await getData(
        start_datetime, end_datetime, size, offset, filter, f"ocp.elasticsearch"
    )
    filterData = await getFilterData(
        start_datetime, end_datetime, filter, f"ocp.elasticsearch"
    )
    print(filterData)
    if not isinstance(response, pd.DataFrame) and response:
        df = response["data"]
        if len(df) == 0:
            return df
        df.insert(len(df.columns), "product", "ocp")
        df["releaseStream"] = df.apply(getReleaseStream, axis=1)
        df["version"] = df["shortVersion"]
        df["testName"] = df["benchmark"]
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": response["total"]}
