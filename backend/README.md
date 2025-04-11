# Local Development

## Configure Environment

### Requires

* [elasticsearch configuration](../README.md#elasticsearch-configuration)
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
pipenv shell
```

Start backend application with hot reload.

```shell
./scripts/start-reload.sh
```

## Using A Debugger

The file `app/entrypoint.py` starts the backend using uvicorn on port 8000.

To use a debugger, run the entrypoint file from the debugger with the appropriate poetry backend.