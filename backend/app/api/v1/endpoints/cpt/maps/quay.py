from ....commons.ocp import getData
from datetime import date


################################################################
# This will return a DataFrame from Quay required by the CPT endpoint
################################################################
async def quayMapper(start_datetime: date, end_datetime: date, configpath: str):
    df = await getData(start_datetime, end_datetime, configpath)
    df.insert(len(df.columns), "product", "quay")
    df["releaseStream"] = df.apply(getReleaseStream, axis=1)
    df["version"] = df["shortVersion"]
    df["testName"] = df["benchmark"]
    return df

def getReleaseStream(row):
    if row["releaseStream"].__contains__("nightly"):
        return "Nightly"
    return "Stable"