const esapi = require('@elastic/elasticsearch')

const MAX_HITS = 1000

const es = new esapi.Client({ 
  node: `http://${process.env.ELASTICSEARCH_URL}`
 })


const jobrun_old =   {
  _index: 'perf_scale_ci',
  _type: '_doc',
  _id: '7HvelHQBbvy-V-Q8z9Gt',
  _score: 1,
  _source: {
    uuid: '3c2d06d0-bd37-4892-a98b-ebe69b69c5be',
    platform: 'AWS',
    master_count: 3,
    worker_count: 4,
    infra_count: 3,
    workload_count: 1,
    total_count: 11,
    cluster_name: 'scale-fipscluster-zp8kq',
    build_tag: 'jenkins-ATS-SCALE-CI-TEST-266',
    node_name: 'scale-ci-slave-1',
    job_status: 'FAILURE',
    build_url: 'https://mastern-jenkins-csb-openshift-qe.cloud.paas.psi.redhat.com/job/ATS-SCALE-CI-TEST/266/',
    job_duration: '18708',
    timestamp: '2020-09-15T23:04:19.713'
  }
}

const jobrun = {
  "uuid" : "38f4ef00-8ad6-4604-a496-50871aed4a76",
  "run_id" : "SCALE-CI-PIPELINE-AWS-4.7-57",
  "platform": "AWS",
  "network_type": "OpenShiftSDN",
  "cluster_version": "4.7.0-0.nightly-2020-12-20-031835",
  "cluster_name": "perfciaws-future-kv5lt",
  "build_tag": "jenkins-ATS-SCALE-CI-SCALE-568",
  "node_name": "scale-ci-slave-4",
  "job_status": "SUCCESS",
  "build_url": "https://mastern-jenkins-csb-openshift-qe.cloud.paas.psi.redhat.com/job/ATS-SCALE-CI-SCALE/568/",
  "upstream_job": "SCALE-CI-PIPELINE-AWS-4.7",
  "upstream_job_build": 57,
  "timestamp": "2020-12-21T10:51:32.489"
}

const now = new Date(2020, 11, 20)
const oldest = new Date(2020, 10, 29)


const fs = require('fs')


async function extract () {

  const result = await es.search({
    // error_trace: true,
    index: 'perf_scale_ci',
    body: {
      query: {
        range: {
          timestamp: {
            // gte: "2020-01-01T00:00:00.000",
            gte: "now-3M",
            lte: "now"
          }
        }
      }
    },
    size: MAX_HITS
  })



  console.log(result.body.hits.total)
  console.log(result.body.hits.hits)
}

extract()