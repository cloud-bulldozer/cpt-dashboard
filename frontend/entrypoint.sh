#!/bin/sh

set -e

# Retry until 'backend' DNS resolves
until getent hosts backend; do
  echo "Waiting for backend DNS resolution..."
  sleep 2
done

# Once backend DNS resolves, start nginx
exec nginx -g "daemon off;"
