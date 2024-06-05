from ....commons.telco import getData
from ....commons.utils import getReleaseStream
from datetime import date


#####################################################################
# This will return a DataFrame from Telco required by the CPT endpoint
#####################################################################
async def telcoMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime, f'telco.splunk')
    if len(df) == 0:
        return df
    df.insert(len(df.columns), "product", "telco")
    df["releaseStream"] = df.apply(getReleaseStream, axis=1)
    df["version"] = df["shortVersion"]
    df["testName"] = df["benchmark"]
    return df
