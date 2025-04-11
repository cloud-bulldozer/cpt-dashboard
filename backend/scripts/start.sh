#!/usr/bin/bash

poetry run uvicorn --host="0.0.0.0" --port=8000 --forwarded-allow-ips='*' --proxy-headers app.main:app
