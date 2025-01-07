from .app.api.v1.commons.telco import getData
from .app.api.v1.commons.utils import getReleaseStream
from datetime import date
import pandas as pd


#####################################################################
# This will return a DataFrame from Telco required by the CPT endpoint
#####################################################################
async def telcoMapper(start_datetime: date, end_datetime: date, size: int, offset: int):
    response = await getData(
        start_datetime, end_datetime, size, offset, f"telco.splunk"
    )
    if not isinstance(response, pd.DataFrame) and response:
        df = response["data"]
        if len(df) == 0:
            return df
        df.insert(len(df.columns), "product", "telco")
        df["releaseStream"] = df.apply(getReleaseStream, axis=1)
        df["version"] = df["shortVersion"]
        df["testName"] = df["benchmark"]
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": 0}
