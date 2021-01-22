#!/usr/bin/bash

uvicorn --port=8000 --forwarded-allow-ips='*' --proxy-headers main:app