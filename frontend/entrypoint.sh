#!/bin/sh
# the performance data api host name is dependent 
# upon its service name as determined in your 
# container orchestration, currently it is 'backend'

set -e

# Retry until 'backend' DNS resolves
until getent hosts backend; do
  echo "Waiting for backend DNS resolution..."
  sleep 2
done

# Once backend DNS resolves, start nginx
exec nginx -g "daemon off;"
