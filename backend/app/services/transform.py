import pandas as pd
import numpy as np
import orjson

from app.models.jobrun import JobRun

from pprint import pprint


def extract_to_long_df(jobrun_jsons: list):
  return pd.DataFrame((
    parse_jobrun(j['_source'])
    for j in jobrun_jsons))

def parse_jobrun(j):
  jr = JobRun(**j)
  jr.build_tag = parse_build_tag(jr.build_tag)
  return jr.dict()
  

def parse_build_tag(build_tag: str):
  return ' '.join(build_tag.split('-')[1:-1]).lower()


def to_ocpapp(es_response):
  df = extract_to_long_df(es_response['hits']['hits'])
  df['platform'] = df['platform'].str.lower()
  print(df)
  return {
    # 'response': long_df_to_ocpapp(df)
    'response': platform_tab_list(df)
  }


def platform_tab(title: str, df: pd.DataFrame):
  return {
    'title': title,
    'data': long_df_to_ocpapp(df)
  }

def platform_tab_list(wide: pd.DataFrame):
  wide['platform'] = wide['platform'].str.lower()
  return [
    platform_tab(g[0], g[1].drop(columns=['platform']))
    for g in wide.groupby(by=['platform'])
  ]


def nest_two(a: np.array):
  return {'title': a[0], 'url': a[1]}


def wider(long: pd.DataFrame, heading_colname: str):
  long['job_status'] = long['job_status'].str.lower()
  long[heading_colname] = long['cluster_version'] + ' ' + long['network_type']
  # long['outcome'] = np.apply_along_axis(nest_two, 1,
    # long[['job_status', 'result']])
  long['outcome'] = long['job_status']
  long = long.drop(
    columns=['cluster_version', 'network_type', 'job_name', 'job_status', 'result'])
  return long.pivot(
    index=['heading',
    # 'platform',
      'timestamp','build_number'],
    columns='build_tag',values='outcome')\
    .reset_index()


def long_df_to_ocpapp(long: pd.DataFrame):
  return ( long
    .pipe(wider, heading_colname='heading')
    .pipe(ocpframelist, heading_colname='heading')
  )


def ocpframe(heading: str, df: pd.DataFrame):
  return {
    'version': heading,
    'cloud_data': df.values.tolist(),
    'columns': df.columns.tolist()
  }
  

def ocpframelist(wide: pd.DataFrame, heading_colname: str):
  return [
    ocpframe(g[0], g[1].drop(columns=[heading_colname])) 
    for g in wide.groupby(by=[heading_colname])
  ]


def main():
  wide = (pd.read_csv('../tests/mocklong2.csv',
                      dtype={
      'cluster_version': 'string',
      'build_number': 'string'
    })
    .pipe(platform_tab_list)
  )
  pprint(wide)
  with open('../tests/tab_wide.json', 'wb') as widened:
    widened.write(orjson.dumps({'response':wide}))


def to_ocpapp_tst(csvpath, jsonpath):
  wide = platform_tab_list(pd.read_csv(csvpath,
    dtype={
      'cluster_version': 'string',
      'build_number': 'string'
    }))
  with open(jsonpath, 'wb') as widened:
    widened.write(orjson.dumps({'response':wide}))


if __name__ == '__main__':
  main()
