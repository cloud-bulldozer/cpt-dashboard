from pprint import pprint
from datetime import datetime

import pandas as pd
import numpy as np
import semver

from app.models.jobrun import JobRun

def build_results_dataframe(raw_es_results, columns=[]):
    docs = raw_es_results["hits"]["hits"]
    jobs = [JobRun(**doc["_source"]).dict() for doc in docs]
    data_frame = pd.DataFrame(jobs)

    data_frame['major_version'] = data_frame['cluster_version'].apply(_get_major_minor_version)
    data_frame['build_version'] = data_frame['cluster_version']
    data_frame['ocp_profile'] = data_frame['major_version'] + ' ' + data_frame['network_type']

    return {
        'response': group_by_platform(data_frame)
    }


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
    get_frame(group[0], flatten(group[1].drop(columns=['ocp_profile'])))
    for group in data_frame.groupby(by=['ocp_profile'])
  ]

def get_frame(title: str, data_frame: pd.DataFrame):
  return {
    'version': title,
    'cloud_data': data_frame.values.tolist(),
    'columns': [name.replace('_', ' ').title()
                for name in data_frame.columns.tolist()]
  }

def flatten(long: pd.DataFrame):
  long['start_date'] = long['start_date'].min().strftime('%b %d, %Y @ %H:%M')
  long['end_date'] = long['end_date'].max().strftime('%b %d, %Y @ %H:%M')
  long['outcome'] = long['job_status']

  return long.pivot(
    index=['build_version', 'upstream_job', 'upstream_job_build', 'start_date', 'end_date' ],
    columns=['build_tag'], values='outcome') \
    .reset_index()



def _get_major_minor_version(version: str):
    parsed_version = semver.VersionInfo.parse(version)
    return f"{parsed_version.major}.{parsed_version.minor}"