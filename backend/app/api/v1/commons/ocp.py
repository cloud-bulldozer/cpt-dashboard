from datetime import date
import pandas as pd
import app.api.v1.commons.utils as utils
from app.services.search import ElasticService
import json

async def getData(start_datetime: date, end_datetime: date, size:int, offset:int, sort:str, filter:str, configpath: str):
    try:
        query = {
            "query": {
                "bool": {
                    "filter":{
                        "range": {
                            "timestamp": {
                                "format": "yyyy-MM-dd"
                            }
                        }
                        
                    }
                }
            }
        }
        es = ElasticService(configpath=configpath)
        if sort:
            query.update({"sort": json.loads(sort)})
        if filter:
            filter_dict = json.loads(filter)
            
        # query['query']['bool']['must'][0].update({"terms":{"platform.keyword":["AWS","GCP"]}})
        print(filter_dict)

        response = await es.post(query=query, size=size, filterTerms=filter_dict, offset=offset, start_date=start_datetime, end_date=end_datetime, timestamp_field='timestamp')
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
        print(f"{type(err).__name__} was raised: {err}") 

async def getFilterData(start_datetime: date, end_datetime: date, size:int, offset:int, sort:str, filter:str, configpath: str):
    try:
        query = {
            "aggs":{
                "min_timestamp":{
                    "min":{
                        "field": start_datetime.strftime('%Y-%m-%d') if start_datetime else (datetime.utcnow().date() - timedelta(days=5).strftime('%Y-%m-%d'))
                    }
                },
                "max_timestamp": {
                    "max": {
                        "field": end_datetime.strftime('%Y-%m-%d') if end_datetime else datetime.utcnow().strftime('%Y-%m-%d')
                    }
                }
            }
        }
        keysDict = {"ciSystem":"ciSystem.keyword","platform":"platform.keyword","benchmark":"benchmark.keyword",
                    "releaseStream":"releaseStream.keyword","networkType":"networkType.keyword", "workerNodesCount":"workerNodesCount","jobStatus":"jobStatus.keyword",
                    "controlPlaneArch":"controlPlaneArch.keyword","publish":"publish.keyword","fips":"fips.keyword","encrypted":"encrypted.keyword",
                    "ipsec":"ipsec.keyword", "ocpVersion":"ocpVersion.keyword", "build":"ocpVersion.keyword",
                    "upstream":"upstreamJob.keyword"
                }         
        
        aggregate = {}         
        
        es = ElasticService(configpath=configpath)
        if sort:
            query.update({"sort": json.loads(sort)})
       
        if filter:
            filter_dict = json.loads(filter)
            if bool(filter_dict):
                filterList = []
                for keyField,value in filter_dict.items():                  
                    obj = {"terms":{keyField:[s if s.isnumeric() else s.upper() for s in value]}}
                    filterList.append(obj)
            query.update({"query":{"bool":{"filter":filterList}}})      
       
        for x,y in keysDict.items():
            obj = {x:{"terms":{"field":y}}}
            aggregate.update(obj)
        query["aggs"].update(aggregate)
        print(query)
        response = await es.filterPost(query=query)
        await es.close()
    
        filterK=[]
        if bool(response):
            for k,v in response.items():
                if k!= "max_timestamp" and k!= "min_timestamp":
                    obj={"key":k}                       
                    for x in v:
                        values=[]
                        buildVal=[]
                        if x == "buckets":
                            buck = v[x]
                            for m in buck:                           
                                if k == "ocpVersion":
                                    values.append(m["key"][0:4])
                                elif k == "build":
                                    values.append("-".join(m["key"].split("-")[-4:]))                            
                                else:
                                    values.append(str(m["key"]).lower())
                            obj.update({"value": values})
                    filterK.append(obj)
            upstreamData = response["upstream"] and response["upstream"]["buckets"]
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
                filterK.append({"key":"jobType", "value":list(set(jobType))})
                filterK.append({"key":"isRehearse","value": list(set(isRehearse))})
            
            filterResponse = [d for d in filterK if d['key']!="upstream"]
            print(filterResponse)
            return (filterResponse)
        return(filterK)
    
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}") 


def fillEncryptionType(row):
    if row["encrypted"] == "N/A":
        return "N/A"
    elif row["encrypted"] == "false":
        return "None"
    else:
        return row["encryptionType"]
