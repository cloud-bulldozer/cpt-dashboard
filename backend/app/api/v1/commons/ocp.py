from datetime import date
import pandas as pd
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService
import json

def buildFilterQuery(filter: dict, query: dict):
    minimum_match = 0
    filter_dict = json.loads(filter)
    if bool(filter_dict):
        for key,val in filter_dict.items():
            if key == "workerNodesCount":
                query["query"]["bool"]["filter"].append({"terms":{"workerNodesCount":val}})
            elif key == "build":    
                for item in filter_dict["build"]:                
                    buildObj = getMatchPhrase("ocpVersion", item) 
                    query["query"]["bool"]["should"].append(buildObj)
                minimum_match+=1
            elif key == "jobType":
                for item in filter_dict["jobType"]:
                    obj = getMatchPhrase("upstreamJob", item)                      
                    query["query"]["bool"]["should"].append(obj)
                minimum_match+=1
            elif key == "isRehearse":
                rehearseObj = {"match_phrase": {"upstreamJob":"rehearse"}}
                if True in filter_dict["isRehearse"]:
                    query["query"]["bool"]["should"].append(rehearseObj)
                    minimum_match+=1
                if False in filter_dict["isRehearse"]:
                    query["query"]["bool"]["must_not"].append(rehearseObj)
            else:
                
                for item in filter_dict[key]:
                    queryObj = getMatchPhrase(key, item) 
                    query["query"]["bool"]["should"].append(queryObj)
                minimum_match+=1
    if len(query["query"]["bool"]["should"]) >= 1:
        query["query"]["bool"].update({"minimum_should_match": minimum_match})
    
    return query    
 
def buildAggregateQuery():
    keysDict = {"ciSystem":"ciSystem.keyword","platform":"platform.keyword","benchmark":"benchmark.keyword",
                    "releaseStream":"releaseStream.keyword","networkType":"networkType.keyword", "workerNodesCount":"workerNodesCount","jobStatus":"jobStatus.keyword",
                    "controlPlaneArch":"controlPlaneArch.keyword","publish":"publish.keyword","fips":"fips.keyword","encrypted":"encrypted.keyword",
                    "ipsec":"ipsec.keyword", "ocpVersion":"ocpVersion.keyword", "build":"ocpVersion.keyword",
                    "upstream":"upstreamJob.keyword"
                }   
    aggregate = {}
    for x,y in keysDict.items():
        obj = {x:{"terms":{"field":y,"size":10}}}
        aggregate.update(obj)   
    return aggregate

async def getData(start_datetime: date, end_datetime: date, size:int, offset:int, sort:str, filter:str, configpath: str):
    try:
        query = {
            "query": {
                "bool": {
                    "filter":[{
                        "range": {
                            "timestamp": {
                                "format": "yyyy-MM-dd"
                            }
                        }
                        
                    }],
                    "should":[],
                    "must_not":[]
                }
            }
        }
        es = ElasticService(configpath=configpath)
       
        if sort:
            query.update({"sort": json.loads(sort)})
        if filter:
            query=buildFilterQuery(filter, query) 
            
        response = await es.post(query=query, size=size, offset=offset, start_date=start_datetime, end_date=end_datetime, timestamp_field='timestamp')
        await es.close()
        tasks = [item['_source'] for item in response["data"]]
        jobs = pd.json_normalize(tasks)
        if len(jobs) == 0:
            return jobs

        jobs[['masterNodesCount', 'workerNodesCount',
            'infraNodesCount', 'totalNodesCount']] = jobs[['masterNodesCount', 'workerNodesCount', 'infraNodesCount', 'totalNodesCount']].fillna(0)
        jobs.fillna('', inplace=True)
        jobs[['ipsec', 'fips', 'encrypted',
            'publish', 'computeArch', 'controlPlaneArch']] = jobs[['ipsec', 'fips', 'encrypted',
                                                                    'publish', 'computeArch', 'controlPlaneArch']].replace(r'^\s*$', "N/A", regex=True)
        jobs['encryptionType'] = jobs.apply(fillEncryptionType, axis=1)
        jobs['benchmark'] = jobs.apply(utils.updateBenchmark, axis=1)
        jobs['platform'] = jobs.apply(utils.clasifyAWSJobs, axis=1)
        jobs['jobType'] = jobs.apply(utils.jobType, axis=1)
        jobs['isRehearse'] = jobs.apply(utils.isRehearse, axis=1)
        jobs['jobStatus'] = jobs.apply(utils.updateStatus, axis=1)
        jobs['build'] = jobs.apply(utils.getBuild, axis=1)

        cleanJobs = jobs[jobs['platform'] != ""]

        jbs = cleanJobs
        jbs['shortVersion'] = jbs['ocpVersion'].str.slice(0, 4)

        return ({"data":jobs,"total":response["total"]})
    
    except Exception as err:
        print(f"{type(err).__name__} was raised14: {err}") 

def getMatchPhrase(key, item):
    buildObj = {"match_phrase": {key: item}}  
    return buildObj
    
def getSummary(jobStatus, isFilterReset):
    if isFilterReset:
        new_dict = {item['key']:0 for item in jobStatus}
    else:
        new_dict = {item['key']:item['doc_count'] for item in jobStatus}     
    return new_dict

async def getFilterData(start_datetime: date, end_datetime: date, size:int, offset:int, sort:str, filter:str, configpath: str):
    try:
        start_date = start_datetime.strftime('%Y-%m-%d') if start_datetime else (datetime.utcnow().date() - timedelta(days=5).strftime('%Y-%m-%d'))
        end_date = end_datetime.strftime('%Y-%m-%d') if end_datetime else datetime.utcnow().strftime('%Y-%m-%d')
        query = {"aggs":{"min_timestamp":{"min":{"field":start_date}},"max_timestamp":{"max":{"field":end_date}}},"query":{"bool":{"filter":[{"range":{"timestamp":{"format":"yyyy-MM-dd","lte":end_date,"gte":start_date}}}],"should":[],"must_not":[]}}}
        
        es = ElasticService(configpath=configpath)
        if bool(sort):
            query.update({"sort": json.loads(sort)})
       
        if bool(filter):
            query = buildFilterQuery(filter, query) 
            
        aggregate = buildAggregateQuery()
        query["aggs"].update(aggregate)
        
        isFilterReset = False
        response = await es.filterPost(query=query)
        metrics = {'total': response["total"]}
        
        if(response["total"] == 0):
            query.pop('query', None)
            response = await es.filterPost(query=query)
            isFilterReset = True
            
        await es.close()    
        filter_=[]
            
        if bool(response) and bool(response["filter_"]):
            for k,v in response["filter_"].items():
                if k!= "max_timestamp" and k!= "min_timestamp":
                    obj={"key":k}                       
                    for x in v:
                        values=[]
                        if x == "buckets":
                            buck = v[x]
                            if k == "jobStatus":                                
                                metrics.update(getSummary(buck, isFilterReset))                                
                            for m in buck:                           
                                if k == "ocpVersion":
                                    values.append(m["key"][0:4])
                                elif k == "build":
                                    values.append("-".join(m["key"].split("-")[-4:]))                        
                                else:
                                    values.append(str(m["key"]).lower())
                            obj.update({"value": values})
                    filter_.append(obj)
                    
            if response["filter_"]["upstream"] and response["filter_"]["upstream"]["buckets"]:
                upstreamData = response["filter_"]["upstream"]["buckets"]
                jobType = []
                isRehearse = []
                if len(upstreamData) > 0:
                    for i in upstreamData:
                        if i["key"].find("periodic"):
                            jobType.append("periodic")
                        else:
                            jobType.append("pull request")
                        if i["key"].find("rehearse"):
                            isRehearse.append("true")
                        else:
                            isRehearse.append("false")
                    filter_.append({"key":"jobType", "value":list(set(jobType))})
                    filter_.append({"key":"isRehearse","value": list(set(isRehearse))})
            
            filterResponse = [d for d in filter_ if d['key']!="upstream"]
              
            return ({"filterData":filterResponse, "summary":metrics})
        return({"filterData":[], "summary":[]})
    
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}") 


def fillEncryptionType(row):
    if row["encrypted"] == "N/A":
        return "N/A"
    elif row["encrypted"] == "false":
        return "None"
    else:
        return row["encryptionType"]
