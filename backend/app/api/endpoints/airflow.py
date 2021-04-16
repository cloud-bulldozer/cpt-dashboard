from fastapi import APIRouter

import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from app.models.airflow import Dag, DagRun
import semver
from app.core import transformv2


router = APIRouter()


@router.post('/api/airflow')
@router.get('/api/airflow')
def airflow():
    
    airflow_url = "http://airflow.apps.keith-cluster.perfscale.devcluster.openshift.com/api/v1/dags"
    response = requests.get(airflow_url, auth=HTTPBasicAuth('admin', 'admin')).json()
    parsed_dags = [{**dag , **parse_id(dag['dag_id']), **get_release_stream(dag['tags'])} for dag in response['dags']]
    dags = [Dag(**dag) for dag in parsed_dags]
    for dag in dags:
        dag.runs = get_runs(dag.dag_id)

    dags = [dag.dict() for dag in dags]
    return transformv2.build_airflow_dataframe(dags) 



def parse_id(dag_id: str): 
    return dict(zip(('version', 'platform', 'profile'), dag_id.split('_')))

def get_release_stream(tags: list):
    for tag in tags:
        if "-stable" in tag['name'] or semver.VersionInfo.isvalid(tag['name']):
            return {"release_stream": tag['name']}
        
    


def get_runs(dag_id: str):
    airflow_url = f"http://airflow.apps.keith-cluster.perfscale.devcluster.openshift.com/api/v1/dags/{dag_id}/dagRuns?limit=10"
    response = requests.get(airflow_url, auth=HTTPBasicAuth('admin', 'admin')).json()
    return [DagRun(**run).dict() for run in response['dag_runs']]

