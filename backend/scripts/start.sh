#!/usr/bin/bash

uvicorn --host="0.0.0.0" --port=8000 --forwarded-allow-ips='*' --proxy-headers app.main:app
