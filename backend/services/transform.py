import pandas as pd
import numpy as np
import orjson

from pprint import pprint


def nest_two(a: np.array):
  return {'verdict': a[0], 'result': a[1]}


def wider(long: pd.DataFrame, heading_colname: str):
  long['heading'] = long['openshift'] + ' ' + long['network']
  long['outcome'] = np.apply_along_axis(nest_two, 1, long[['verdict', 'result']])
  long = long.drop(columns=['openshift', 'network', 'verdict', 'result'])
  return long.pivot(
    index=['heading','platform', 'build_date',
      'run_date', 'job','build_id'],
    columns='workload',values='outcome')\
    .reset_index()


def ocpframe(heading: str, df: pd.DataFrame):
  return {
    'version': heading,
    'cloud_data': df.values.tolist()
  }
  

def ocpframelist(wide: pd.DataFrame, heading_colname: str):
  return [
    ocpframe(g[0], g[1]) 
    for g in wide.groupby(by=[heading_colname])
  ]


def main():
  wide = (pd.read_csv('../tests/mocklong.csv',
    dtype={
      'openshift': 'string',
      'build_id': 'string'
    })
    .pipe(wider, heading_colname='heading')
    .pipe(ocpframelist, heading_colname='heading')
  )
  pprint(wide)
  # print(orjson.dumps(wide))


if __name__ == '__main__':
  main()
