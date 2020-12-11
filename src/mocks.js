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

const cloud_data = [
  ['aws', ...dates, ...results],
  ['aws future', ...dates, ...results]
]

const ocpdata = [
  {version: '4.6 nightly', cloud_data: cloud_data},
  {version: '4.6 ovn nightly', cloud_data: cloud_data},
  {version: '4.7 nightly', cloud_data: cloud_data},
  {version: '4.7 ovn nightly', cloud_data: cloud_data},
  {version: '4.8 nightly', cloud_data: cloud_data}
]

const dates2 = [
  {title:'01/01/2021'}, {title:'01/02/2021'}
]

const results2 = [
  {title: 'success', url: 'https://www.redhat.com'},
  {title: 'warning', url: 'https://www.redhat.com'},
  {title: 'failure', url: 'https://www.redhat.com'}, 
  {title: 'success', url: 'https://www.redhat.com'},
  {title: 'success', url: 'https://www.redhat.com'},
  {title: 'success', url: 'https://www.redhat.com'},
  {title: 'success', url: 'https://www.redhat.com'},
]

const cloud_data2 = [
  ['aws', ...dates, ...results2],
  ['aws next', ...dates, ...results2],
  ['aws future', ...dates, ...results2],
  ['aws 2 electric boogaloo ', ...dates, ...results2],
  ['aws tron', ...dates, ...results2],
  ['aws tron legacy', ...dates, ...results2],
  ['gcp redux', ...dates, ...results2]
]

const ocpdata2 = [
  {version: '4.6 nightly', cloud_data: cloud_data2},
  {version: '4.6 ovn nightly', cloud_data: cloud_data2},
  {version: '4.7 nightly', cloud_data: cloud_data2},
  {version: '4.7 ovn nightly', cloud_data: cloud_data2},
  {version: '4.8 nightly', cloud_data: cloud_data2}
]

export { data, ocpdata, ocpdata2 };