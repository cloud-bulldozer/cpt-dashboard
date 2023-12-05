from ....commons.hce import getData
from datetime import date

################################################################
# This will return a DataFrame from HCE required by the CPT
#  endpoint, it contians the following columns:
#   "ciSystem"
#   "uuid"
#   "releaseStream"
#   "jobStatus"
#   "buildUrl"
#   "startDate"
#   "endDate"
#   "product"
#   "version"
#   "testName"
################################################################
async def hceMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime)
    df["releaseStream"] = "Nightly"
    df["ciSystem"] = "Jenkins"
    df["testName"] = df["test"]
    df["jobStatus"] = df['result'].apply(lambda x: "SUCCESS" if x == 'PASS' else "FAILURE")
    df["version"] = df['version'].apply(lambda x: x if len(x.split(":")) == 1 else x.split(":")[1][:7])
    df["uuid"] = df["result_id"]
    df["buildUrl"] = df["link"]
    df["startDate"] = df["date"]
    df["endDate"] = df["date"]
    df = dropColumns(df)
    return df


def dropColumns(df):
    df = df.drop(columns=["group","test","result","result_id","link","date","release"])
    return df
