from .app.api.v1.commons.hce import getData
from datetime import date
import pandas as pd


################################################################
# This will return a Dictionary from HCE required by the CPT
#  endpoint, it contians totalJobs and a Dataframe with the following columns:
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
async def hceMapper(start_datetime: date, end_datetime: date, size: int, offset: int):
    response = await getData(
        start_datetime, end_datetime, size, offset, f"hce.elasticsearch"
    )
    if response:
        df = response["data"]
        if len(df) == 0:
            return df
        df["releaseStream"] = "Nightly"
        df["ciSystem"] = "Jenkins"
        df["testName"] = df["product"] + ":" + df["test"]
        df["product"] = df["group"]
        df["jobStatus"] = df["result"].apply(
            lambda x: "SUCCESS" if x == "PASS" else "FAILURE"
        )
        df["version"] = df["version"].apply(
            lambda x: x if len(x.split(":")) == 1 else x.split(":")[1][:7]
        )
        df["uuid"] = df["result_id"]
        df["buildUrl"] = df["link"]
        df["startDate"] = df["date"]
        df["endDate"] = df["date"]
        df = dropColumns(df)
        return {"data": df, "total": response["total"]}
    return {"data": pd.DataFrame(), "total": 0}


def dropColumns(df):
    df = df.drop(
        columns=["group", "test", "result", "result_id", "link", "date", "release"]
    )
    return df
