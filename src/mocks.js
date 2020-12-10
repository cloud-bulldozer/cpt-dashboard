const success = {
  result: 'success', datatable: 'www.google.com'
}
const warning = {
  result: 'warning', datatable: 'www.google.com'
}
const failure = {
  result: 'failure', datatable: 'www.google.com'
}

const results_dict = {
  build: success, install: warning, uperf: failure,
  http: success, kubelet: success, object_density: success,
  upgrade: success
}

const dates_dict = {
  build_date: '01/01/2021', run_date: '01/02/2021'
}

const dates = [
  '01/01/2021', '01/02/2021'
]

const results = [
  'success', 'warning', 'failure', 'success', 'success', 'success', 'success'
]

const data_dict = [
  {
    ocp_version: '4.6 nightly', cloud_pipeline: 'aws', 
    ...dates, ...results
  },
  {
    ocp_version: '4.6 nightly', cloud_pipeline: 'aws future', 
    ...dates, ...results
  },
  {
    ocp_version: '4.6 ovn nightly', cloud_pipeline: 'aws', 
    ...dates, ...results
  },
  {
    ocp_version: '4.7 nightly', cloud_pipeline: 'aws', 
    ...dates, ...results
  },
  {
    ocp_version: '4.7 ovn nightly', cloud_pipeline: 'aws', 
    ...dates, ...results
  },
  {
    ocp_version: '4.8 nightly', cloud_pipeline: 'aws', 
    ...dates, ...results
  }
]


const data = [
  [
    '4.6 nightly', 'aws', 
    ...dates, ...results
  ],
  [
    '4.6 nightly', 'aws future', 
    ...dates, ...results
  ],
  [
    '4.6 ovn nightly', 'aws', 
    ...dates, ...results
  ],
  [
    '4.7 nightly', 'aws', 
    ...dates, ...results
  ],
  [
    '4.7 ovn nightly', 'aws', 
    ...dates, ...results
  ],
  [
    '4.8 nightly', 'aws', 
    ...dates, ...results
  ]
]

export { data };