#!/usr/bin/bash
LOG=${CPT_BACKEND_LOG_LEVEL:-info}
uvicorn --reload --log-level="${LOG}" --host="0.0.0.0" --port=8000 --forwarded-allow-ips='*' --proxy-headers app.main:app
