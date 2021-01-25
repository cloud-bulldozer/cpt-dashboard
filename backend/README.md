# Local Development

## Configure Environment

### Application Configuration

*Deprecated*. Will be refactored to use [TOML](https://toml.io/en/) format.

Create an `ini` format file, name it `ocpperf.cfg`, and then fill in these blanks.


```ini
[elasticsearch]
url=
indice=
username=
password=

[ocp-server]
port=
```

Add an environment variable to tell the application where it's configuration file is.

```shell
export _OCP_SERVER_CONFIG_="$PWD"/ocpperf.cfg
```


### Install Dependencies

#### Requires

* `pwd` is `backend/`
* pipenv

Add `app` directory as a module that can be found by the Python importer.
  
```shell
export PYTHONPATH=$PWD
```

Install application dependencies.

```shell
pipenv install
```

## Start Coding

### Requires

* `pwd` is `backend/`

Start development environment.

```shell
cd app
pipenv shell
```

Start backend application with hot reload.

```shell
./scripts/start-reload.sh
```