from ....commons.ocm import getData
from datetime import date


################################################################
# This will return a DataFrame from OCM required by the CPT endpoint
################################################################
async def ocmMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime, f"ocm.elasticsearch")
    if len(df) == 0:
        return df
    df.insert(len(df.columns), "product", "ocm")
    df.insert(len(df.columns), "releaseStream", "Nightly")
    df["testName"] = df["attack"]
    df["startDate"] = df["metrics.earliest"]
    df["endDate"] = df["metrics.end"]

    return df
