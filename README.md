# OpenShift Performance Dashboard

## Backend configuration

### Requires

* current working directory is `backend/`

Create a configuration file, named **ocpperf** with the following key structure, and fill in the values:

```toml
[<product>.elasticsearch]
url=
indice=
username=
password=

[<product>.splunk]
host=
port=
indice=
username=
password=

[<product>.crucible]
url=
username=
password=

[ocp-server]
port=8000

[jira]
url=
personal_access_token=

[horreum]
url=
username=
password=

[airflow]
url=
username=
password=
```

[TOML](https://toml.io/en/) is used above, but it also accepts YAML.

The backend configuration should be set up by product and its data store type, that way each product can configure their own backend server.

As an example for `OCP` with its ES configuration looks like this:

```toml
[ocp.elasticsearch]
url=
indice=
username=
password=
```
**Note: The below applies only for the elastic search at the moment**
If you also have an archived internal instance that keeps track of older data, it can be specified with '.internal' suffix. Example of our `OCP` internal archived instance's configuration.
```toml
[ocp.elasticsearch.internal]
url=
indice=
# [optional] common prefix for all indexes
prefix=
username=
password=
```

Internally the API when serving the `/ocp` enpoints will use this connection. Also it is suggested to create indexes with same name in the archived instances too to avoid further complications.

The `jira` configuration requires a `url` key and a `personal_access_token` key. The `url` is a string value that points to the URL address of your Jira resource. The [Personal Access Token](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html) is a string value that is the credential issued to authenticate and authorize this application with your Jira resource.

```toml
[jira]
url=""
personal_access_token=""
```

The `horreum` configuration requires the `url` of a running Horreum server,
along with the `username` and `password` to be used to authenticate Horreum
queries.

All `GET` calls to `/api/v1/horreum/api/{path}` will be passed through to
Horreum, including query parameters, and Horreum's response will be returned
to the caller. For example, `GET /api/v1/horreum/api/test/{id}` will return the
same response as directly calling `GET {horreum.url}/api/test/{id}` with the
configured Horreum credentials.

```toml
[horreum]
url="http://localhost:8080"
username="user"
password="secret"
```


## Development on System

1. Follow [backend setup readme](backend/README.md)
2. Follow [frontend setup readme](frontend/README.md)

## Development in Containers

### Requires

* podman

### Build Backend

#### Requires

* current working directory is `backend/`

Build backend image.

```sh
$ podman build \
  --tag ocpp-back \
  --file backend.containerfile \
  .
```

### Run Backend

Run the backend container and attach source code as a writable volume.

```sh
$ podman run \
    --interactive \
    --tty \
    --volume "$PWD/app:/backend/app:z" \
    --volume "$PWD/ocpperf.toml:/backend/ocpperf.toml" \
    --publish 8000:8000 \
    ocpp-back /backend/scripts/start-reload.sh
```

### Build Frontend

#### Requires

* current working directory is `frontend/`

Build frontend image.

```sh
$ podman build \
    --tag ocpp-front \
    --file frontend.containerfile \
    .
```

### Run Frontend

#### Requires

* second terminal
* current working directory is `frontend/`

Run frontend container and attach source code as a writable volume.

```sh
$ podman run \
    --interactive \
    --tty \
    --volume "$PWD:/app:z" \
    --publish 3000:3000 \
    ocpp-front
```

## ES Integration to the dashboard

To integrate into our dashboard we provide a default set of fields that teams should adhere to. That set would be the one used to display a high level Homepage for all the teams.

### Necessary fields

* _ciSystem_: In which system the job ran. E.g.: Jenkins, PROW, Airflow, etc…
* _product_: Which product was this job executed for
* _uuid_: Unique Job Identifier
* _releaseStream_: Where are you getting your built assets tested from. E.G.: nightly, candidate, stable, GA, beta, alpha, etc…
* _version_: This should be a new field, should represent the version of the product you are testing.
* _testName_: Name of the test you are running, in OCP case it would be the benchmark that ran.
* _jobStatus_: The status of the job once it has finished, at least should have failure or success, any other state will be merged into Others category
* _buildUrl_: URL that links to your job.
* _startDate_: Start time of the job
* _endDate_: End time of the job

### How to integrate

For teams to integrate into the dashboard they will need to cover key points to get their data to be shown in the main Homepage.

> Additionally if they want to have a more detailed Dashboard that suits better everyday, they would have to add their custom pages to the UI. We already provide some reusable components that could help them build their custom page.

#### Backend

##### Data sources

OCP PerfScale stores data in [Open/Elastic]search, so there is already a service there to query it, the support multiple ES sources exists, and this is what it’s needed:

There must exist a team configuration for ES credentials in this form in the config file

```toml
[<product>.elasticsearch]
url=
indice=
username=
password=
```

That config file is going to be passed to this [service](https://github.com/cloud-bulldozer/cpt-dashboard/blob/1ce837ae17e0d3fa63f59c751078990b018905dc/backend/app/services/search.py#L11) as the config path to search for the values.

A team using a different backend will need to provide the code to enable utilization of said backend.
> This should be done in a generic way so if other teams use the same they can reuse the code.

##### Endpoint

Steps for adding the data to the result of `/api/v1/cpt/jobs` endpoint

1. Create a custom mapper that will query your data backend and do the appropriate transformations for the data to match the fields described above.
This Mapper should always receive:
   * _start_datetime_, format `YYYY-MM-DD`
   * _end_datetime_, format `YYYY-MM-DD`
This mapper should return
   * A pandas DataFrame

2. In the `/api/v1/cpt/jobs` endpoint add the entry to the [`products`](https://github.com/cloud-bulldozer/cpt-dashboard/blob/1ce837ae17e0d3fa63f59c751078990b018905dc/backend/app/api/v1/endpoints/cpt/cptJobs.py#L12) dictionary that has the different data sources configured, the endpoint should query all configured mappers and append the resulting DataFrames to the overall response.

##### Frontend

An overview of personas that the dashboard is thought for:

* _Product_: Its main source of information comes from `/home` high level overview across products.
* _Team Lead/Manager_: Focused on a single product, its main source of information will come from the dedicated dashboard, for OCP PerfScale it would be `/ocp`, there it will have more details of each job, being able to see basic metrics.
* _PerfScale/QE Engineer_: Focused on reviewing the job that ran, to check if issues happened, review logs, and access detailed dashboard. For the OCP PerfScale team apart from seeing the job details and basic metrics he would like to go to a specialized Grafana dashboard and go directly to the job to read the logs.

###### Only a Hub (Product)

If your goal is to get all your jobs results in one place, and be able to filter by CI-System, test, product, status and release stream, the described backend steps should be the only ones you take, once deployed the backend should provide all the data to the frontend and it should be displayed, providing links to the jobs that have run.

###### Specialized view (Team Leads/Managers/Engineers)

For the specialized view, Teams will need to provide most of the code for it:

1. Choose a path for your team, `/home` and `/ocp` are already reserved.
2. You’ll need to code a small stateful React frontend to display your custom view, we provide some reusable components for a home view, they may or may not suit you:
   * State object
   * Reducer for the data
   * In a NEW folder inside the components section of the frontend app add your react components for your view
   * Always be sure to provide a way back to the general dashboard. I.e.: Don’t remove the top navigation bar.
   * Think of reusable components, maybe you can help other teams after you.
   * If you need new endpoints for this you’ll need to add/code them to the backend API:
     * Written in Python
     * Using fastAPI
     * Document endpoints with swagger

## Internal process

For the purpose of adding new configuration and authentication credentials to the API, plase follow the steps below

* Create a new Jira ticket under the `PERFSCALE` namespace
* In the name of the ticket please set up `[Dashboard]` at the start
* Include in the epic `PERFSCALE-2250`
* Include the complete configuration to add, example:

  ```toml
  [<product>.elasticsearch]
  url=https://real.es.com
  indice=mydata
  username=admin
  password=password123
  ```

* Assign the ticket to `vzepedam@redhat.com`
* Add as watcher `jtaleric@redhat.com`
