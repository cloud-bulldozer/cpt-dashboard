#!/usr/bin/bash

uvicorn --reload --port=8000 --forwarded-allow-ips='*' --proxy-headers main:app