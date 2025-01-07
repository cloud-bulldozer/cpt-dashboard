from .app.api.v1.commons.ocm import getData
from datetime import date
import pandas as pd


################################################################
# This will return a DataFrame from OCM required by the CPT endpoint
################################################################
async def ocmMapper(start_datetime: date, end_datetime: date, size: int, offset: int):
    response = await getData(
        start_datetime, end_datetime, size, offset, f"ocm.elasticsearch"
    )
    if not isinstance(response, pd.DataFrame) and response:
        df = response["data"]
        if len(df) == 0:
            return df
        df.insert(len(df.columns), "product", "ocm")
        df.insert(len(df.columns), "releaseStream", "Nightly")
        df["testName"] = df["attack"]
        df["startDate"] = df["metrics.earliest"]
        df["endDate"] = df["metrics.end"]
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": 0}
