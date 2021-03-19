from pprint import pprint
from datetime import datetime

import pandas as pd
import numpy as np

from app.models.jobrun import JobRun


def extract_to_long_df(jobrun_jsons: list):
  return pd.DataFrame((
    parse_jobrun(j['_source'])
    for j in jobrun_jsons))


def parse_jobrun(j):
  jr = JobRun(**j)
  if jr.build_tag is None:
    jr.build_tag = jr.job_name
  return jr.dict()
  

def parse_build_tag(build_tag: str) -> str:
  return ' '.join(build_tag.split('-')[1:-1])


def parse_upstream_job(upstream_tag: str) -> str:
  return ' '.join(upstream_tag.split('-')[:-1])


def to_ocpapp(es_response):
  df = extract_to_long_df(es_response['hits']['hits'])
  df[df.drop(columns=['network_type']).select_dtypes(include='object').columns] = df[df.select_dtypes(include='object').columns].drop(['network_type'], axis=1).apply(lambda x: x.str.lower())
  df['build_tag'] = df['build_tag'].apply(parse_build_tag)

  df['upstream_job'] = df['upstream_job'] + '-' + df['upstream_job_build']
  df = df.drop(columns=['upstream_job_build'])

  df['ocp_profile'] = df['cluster_version'] + ' ' + df['network_type']
  df = df.drop(columns=['cluster_version', 'network_type'])

  return {
    'response': by_platform(df)
  }


def nest_two(a: np.array):
  return {'title': a[0], 'url': a[1]}


def myfunc(x):
  print(type(x))
  # x['timestamp'] = x['timestamp'].min()


def widerr(long: pd.DataFrame):
  # long['outcome'] = np.apply_along_axis(nest_two, 1,
  # long[['job_status', 'result']])

  # TODO: group by upstream_job, then set timestamp
  long['timestamp'] = long['timestamp'].min()
  long['timestamp'] = long['timestamp'].dt.strftime('%b %d, %Y @ %H:%M')
  # long['timestamp'] = long.groupby('upstream_job').transform(myfunc)
  # pprint(long.groupby('upstream_job').apply(myfunc))
  
  


  # pd.to_datetime(long['timestamp'], format='%Y-%m-%d %H-%M-%S')
  # long['timestamp'] = long['timestamp'].apply(datetime.fromtimestamp)
  # print(pd.to_datetime(long['timestamp'], format='%Y-%m-%d %H-%M-%S'))
  

  # pprint(long)

  long['outcome'] = long['job_status']
  long = long.drop(
    columns=['job_status', 'result'])
  return long.pivot(
    index=['timestamp', 'upstream_job'],
    columns='build_tag', values='outcome') \
    .reset_index()


def frame(title: str, df: pd.DataFrame):
  return {
    'version': title,
    'cloud_data': df.values.tolist(),
    'columns': df.columns.tolist()
  }


def framelist(df: pd.DataFrame):
  return [
    frame(g[0], g[1].drop(columns=['ocp_profile']).pipe(widerr))
    for g in df.groupby(by=['ocp_profile'])
  ]


def tab(title: str, df: pd.DataFrame):
  return {
    'title': title,
    'data': framelist(df)
  }


def by_platform(df: pd.DataFrame):
  return [
    tab(g[0], g[1].drop(columns=['platform']))
    for g in df.groupby(by=['platform'])
  ]


def main():
  pass


if __name__ == '__main__':
  main()
