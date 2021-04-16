from pprint import pprint
from datetime import datetime

import pandas as pd
import numpy as np
import semver

def build_airflow_dataframe(dags): 


    data_frame = pd.DataFrame(dags)
    runs = [dag['runs'] for dag in dags]
    runs = [run for run_list in runs for run in run_list]
    run_dataframe = pd.DataFrame(runs).drop(columns=['conf', 'external_trigger'])
    
    
    data_frame = data_frame.drop(columns=['tags', 'runs'])
    merged_data_frame = pd.merge(data_frame, run_dataframe, on='dag_id', how='left')
    merged_data_frame['profile_and_version'] = merged_data_frame['version'] + " " + merged_data_frame['profile']
    print(merged_data_frame)
    return { 'response': group_by_platform(merged_data_frame) } 

def group_by_platform(data_frame: pd.DataFrame):
    return [
        get_table(group[0], group[1].drop(columns=['platform']))
        for group in data_frame.groupby(by=['platform'])
    ]

def get_table(title: str, data_frame: pd.DataFrame):
  return {
    'title': title,
    'data': get_framelist(data_frame)
  }

def get_framelist(data_frame: pd.DataFrame):
  return [
    get_frame(group[0], (group[1].drop(columns=['profile_and_version'])))
    for group in data_frame.groupby(by=['profile_and_version'])
  ]

def get_frame(title: str, data_frame: pd.DataFrame):
  print(data_frame.columns)
  return {
    'version': title.title(),
    'cloud_data': data_frame.values.tolist(),
    'columns': [name.replace('_', ' ').title()
                for name in data_frame.columns.tolist()]
  }

def flatten(long: pd.DataFrame):
  return long.pivot(
    index=['dag_id', 'version', 'release_stream']) \
    .reset_index()




