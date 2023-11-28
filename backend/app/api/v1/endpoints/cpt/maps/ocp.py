from ....commons.ocp import getData
from datetime import date


################################################################
# This will return a DataFrame from OCP required by the CPT
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
async def ocpMapper(start_datetime: date, end_datetime: date):
    df = await getData(start_datetime, end_datetime)
    df.insert(len(df.columns), "product", "ocp")
    df["releaseStream"] = df.apply(getReleaseStream, axis=1)
    df["version"] = df["shortVersion"]
    df["testName"] = df["benchmark"]
    df = dropColumns(df)
    return df


def dropColumns(df):
    df = df.drop(columns=['shortVersion', 'benchmark', 'platform', 'clusterType', 'masterNodesCount',
                          'workerNodesCount', 'infraNodesCount', 'masterNodesType', 'workerNodesType',
                          'infraNodesType', 'totalNodesCount', 'clusterName', 'ocpVersion', 'networkType',
                          'buildTag', 'upstreamJob', 'upstreamJobBuild', 'executionDate', 'jobDuration',
                          'timestamp', 'jobType', 'isRehearse'])
    return df


def getReleaseStream(row):
    if row["releaseStream"].__contains__("fast"):
        return "Fast"
    elif row["releaseStream"].__contains__("stable"):
        return "Stable"
    elif row["releaseStream"].__contains__("eus"):
        return "EUS"
    elif row["releaseStream"].__contains__("candidate"):
        return "Release Candidate"
    elif row["releaseStream"].__contains__("rc"):
        return "Release Candidate"
    elif row["releaseStream"].__contains__("nightly"):
        return "Nightly"
    elif row["releaseStream"].__contains__("ci"):
        return "ci"
    elif row["releaseStream"].__contains__("ec"):
        return "Engineering Candidate"
    return "Stable"
