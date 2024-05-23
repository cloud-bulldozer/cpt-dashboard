from ....commons.quay import getData
from datetime import date


#####################################################################
# This will return a DataFrame from Quay required by the CPT endpoint
#####################################################################
async def quayMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime, f'quay.elasticsearch')
    df.insert(len(df.columns), "product", "quay")
    df["version"] = df["releaseStream"]
    df["testName"] = df["benchmark"]
    return df
