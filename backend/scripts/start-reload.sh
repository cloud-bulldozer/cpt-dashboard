#!/bin/bash
scripts/version.py
uvicorn --reload --host="0.0.0.0" --port=8000 --forwarded-allow-ips='*' --proxy-headers app.main:app
