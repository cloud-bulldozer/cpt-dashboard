from app.services.search import ElasticService

async def getMetadata(uuid: str, configpath: str) :
    query = {
        "query": {
            "query_string": {
                "query": (
                    f'uuid: "{uuid}"')
            }
        }
    }
    print(query)
    es = ElasticService(configpath=configpath)
    response = await es.post(query=query)
    await es.close()
    meta = [item['_source'] for item in response]
    return meta[0]

def updateStatus(job):
    return job["jobStatus"].lower()


def updateBenchmark(job):
    if job["upstreamJob"].__contains__("upgrade"):
        return "upgrade-" + job["benchmark"]
    return job["benchmark"]


def jobType(job):
    if job["upstreamJob"].__contains__("periodic"):
        return "periodic"
    return "pull request"


def isRehearse(job):
    if job["upstreamJob"].__contains__("rehearse"):
        return "True"
    return "False"


def clasifyAWSJobs(job):
    if job["upstreamJob"].__contains__("rosa-hcp"):
        return "AWS ROSA-HCP"
    if job["clusterType"].__contains__("rosa"):
        return "AWS ROSA"
    return job["platform"]


def getBuild(job):
    releaseStream = job["releaseStream"] + "-"
    ocpVersion = job["ocpVersion"]
    return ocpVersion.replace(releaseStream, "")