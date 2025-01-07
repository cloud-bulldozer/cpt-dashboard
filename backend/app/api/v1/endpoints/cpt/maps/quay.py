from .app.api.v1.commons.quay import getData
from datetime import date
import pandas as pd


#####################################################################################
# This will return a DataFrame from Quay required by the CPT endpoint with Total jobs
#####################################################################################
async def quayMapper(start_datetime: date, end_datetime: date, size: int, offset: int):
    response = await getData(
        start_datetime, end_datetime, size, offset, f"quay.elasticsearch"
    )
    if not isinstance(response, pd.DataFrame) and response:
        df = response["data"]
        if len(df) == 0:
            return df
        df.insert(len(df.columns), "product", "quay")
        df["version"] = df["releaseStream"]
        df["testName"] = df["benchmark"]
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": 0}
