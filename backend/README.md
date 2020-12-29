# backend

## Requirements

* Python 3.9
* pipenv

## Development

Configure dependencies

    $ pipenv install

Activate environment

    $ pipenv shell

Start ASGI server with application with source code hot reloading

    $ uvicorn --reload --host localhost --port 8000 main:app

Above are the default `host` and `port` values. They are made explicit for clarity.
