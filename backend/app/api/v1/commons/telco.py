from datetime import date
import pandas as pd
from app import config
from app.services.splunk import SplunkService
import app.api.v1.commons.hasher as hasher
from datetime import datetime, timezone
import app.api.v1.commons.utils as utils
import app.api.v1.endpoints.telco.telcoGraphs as telcoGraphs


async def getData(start_datetime: date, end_datetime: date, configpath: str):
    test_types = ["oslat", "cyclictest", "cpu_util", "deployment", "ptp", "reboot", "rfc-2544"]
    cfg = config.get_config()
    try:
        jenkins_url = cfg.get('telco.config.job_url')
    except Exception as e:
        print(f"Error reading telco configuration: {e}")
    test_type_execution_times = {
        "oslat": 3720,
        "cyclictest": 3720,
        "cpu_util": 6600,
        "deployment": 3720,
        "ptp": 4200,
        "reboot": 1980,
        "rfc-2544": 5580,
    }
    query = {
        "earliest_time": "{}T00:00:00".format(start_datetime.strftime('%Y-%m-%d')),
        "latest_time": "{}T23:59:59".format(end_datetime.strftime('%Y-%m-%d')),
        "output_mode": "json"
    }
    searchList = ' OR '.join(['test_type="{}"'.format(test_type) for test_type in test_types])
    splunk = SplunkService(configpath=configpath)
    response = await splunk.query(query=query, searchList=searchList)
    mapped_list = []

    for each_response in response:
        end_timestamp = int(each_response['timestamp'])
        test_data = each_response['data']
        threshold = await telcoGraphs.process_json(test_data, True)
        hash_digest, encrypted_data = hasher.hash_encrypt_json(each_response)
        execution_time_seconds = test_type_execution_times.get(test_data['test_type'], 0)
        start_timestamp = end_timestamp - execution_time_seconds
        start_time_utc = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
        end_time_utc = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
        kernel = test_data['kernel'] if 'kernel' in test_data else "Undefined"

        mapped_list.append({
            "uuid": hash_digest,
            "encryptedData": encrypted_data.decode('utf-8'),
            "ciSystem": "Jenkins",
            "benchmark": test_data['test_type'],
            "kernel": kernel,
            "shortVersion": test_data['ocp_version'],
            "ocpVersion": test_data['ocp_build'],
            "releaseStream": utils.getReleaseStream({'releaseStream': test_data['ocp_build']}),
            "nodeName": test_data['node_name'],
            "cpu": test_data['cpu'],
            'formal': test_data['formal'],
            "startDate": str(start_time_utc),
            "endDate": str(end_time_utc),
            "buildUrl": jenkins_url + "/" + str(test_data['cluster_artifacts']['ref']['jenkins_build']),
            "jobStatus": "failure" if (threshold != 0) else "success",
            "jobDuration": execution_time_seconds,
        })

    jobs = pd.json_normalize(mapped_list)
    if len(jobs) == 0:
        return jobs

    return jobs
