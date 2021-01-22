import pandas as pd
import numpy as np
import orjson

from pprint import pprint


def nest_two(a: np.array):
  return {'title': a[0], 'url': a[1]}


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
    ocpframe(g[0], g[1].drop(columns=[heading_colname])) 
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
  with open('../tests/widened2.json', 'wb') as widened:
    widened.write(orjson.dumps({'data':wide}))


def to_ocpapp(long: pd.DataFrame):
  return ( long
    .pipe(wider, heading_colname='heading')
    .pipe(ocpframelist, heading_colname='heading')
  )


def to_ocpapp_tst(csvpath, jsonpath):
  wide = to_ocpapp(pd.read_csv(csvpath,
    dtype={
      'openshift': 'string',
      'build_id': 'string'
    }))
  with open(jsonpath, 'wb') as widened:
    widened.write(orjson.dumps({'data':wide}))

# Fuqing added
def to_ocp_data(response):
  res = {}
  indices_list = response["hits"]["hits"]
  for indice in indices_list:
      indice = indice["_source"]

      if "cluster_version" in indice and "network_type" in indice:
        network = indice["network_type"].replace("Kubernetes", "").replace("OpenShift","")
        version = ".".join(indice["cluster_version"].split(".")[:2])
        version_id = version + " " + network

        # should have 10 fields
        cloud_data = []
        # 1. platform
        if "platform" in indice:
          cloud_data.append(indice["platform"])
        else:
          cloud_data.append("N/A")

        # 2. build date !!! missing
        if "timestamp" in indice:
          cloud_data.append(indice["timestamp"])
        else:
          cloud_data.append("N/A")

        # 3. run date 
        if "timestamp" in indice:
          cloud_data.append(indice["timestamp"])
        else:
          cloud_data.append("N/A")

        # 4. job
        if "job_name" in indice:
          cloud_data.append(indice["job_name"])
        else:
          cloud_data.append("N/A")

        # 5. build id !! deprecated
        if "build_number" in indice:
          cloud_data.append(indice["build_number"])
        else:
          cloud_data.append("N/A")

        # 6. build !! hard coded right now
        if "job_status" in indice:
          cloud_data.append(indice["job_status"].lower())
        else:
          cloud_data.append("N/A")

        if "build_tag" in indice:
          workload = indice["build_tag"]
          # 7. install
          if "INSTALL" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")

          # 8. uperf
          if "UPERF" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")

          # 9. http
          if "HTTP" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")

          # 10. kublet
          if "KUBLET" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")

          # 11. object density
          if "DENSITY" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")

          # 12. upgrade
          if "UPGRADE" in workload:
            cloud_data.append(indice["job_status"].lower())
          else:
            cloud_data.append("N/A")
        else:
          continue

        if version_id not in res:
          res[version_id] = []
        res[version_id].append(cloud_data)

      else:
        continue

  # additional parsing
  res_list = []
  for key, value in res.items():
    res_list.append({'version': key, 'cloud_data': value})

  return {"response": res_list}

if __name__ == '__main__':
  main()
