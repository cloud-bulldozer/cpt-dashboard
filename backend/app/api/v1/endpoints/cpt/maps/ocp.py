from ....commons.ocp import getData
from ....commons.utils import getReleaseStream
from datetime import date


################################################################
# This will return a DataFrame from OCP required by the CPT endpoint
################################################################
async def ocpMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime, f"ocp.elasticsearch")
    if len(df) == 0:
        return df
    df.insert(len(df.columns), "product", "ocp")
    df["releaseStream"] = df.apply(getReleaseStream, axis=1)
    df["version"] = df["shortVersion"]
    df["testName"] = df["benchmark"]
    return df
