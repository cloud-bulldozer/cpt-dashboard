#!/bin/sh
#
# Simple script to build and publish development containers for the backend
# and frontend components.
#
# Please don't edit this file for debugging: it's too easy to accidentally
# commit undesirable changes. Instead, I've added some convenient environment
# variables to support common changes:
#
# REGISTRY -- container registry (docker.io, quay.io)
# ACCOUNT -- user account (presumed to be logged in already)
# REPO -- account container repo (cpt)
# TAG -- container tag (latest)
# SKIP_FRONTEND -- SKIP_FRONTEND=1 to skip building and pushing frontend
# SKIP_BACKEND -- SKIP_BACKEND=1 to skip building and pushing backend
#
REGISTRY=${REGISTRY:-images.paas.redhat.com}
ACCOUNT=${ACCOUNT:-${USER}}
REPO=${REPO:-cpt}
TAG=${TAG:-latest}
SKIP_FRONTEND=${SKIP_FRONTEND:-0}
SKIP_BACKEND=${SKIP_BACKEND:-0}

REPOSITORY=${REGISTRY}/${ACCOUNT}/${REPO}
# remove current images, if any
podman rm -f front back
now=$(date +'%Y%m%d-%H%M%S')

if [ "$SKIP_BACKEND" != 1 ] ;then
  podman build -f backend/backend.containerfile --tag backend
  podman push backend "${REPOSITORY}/backend:${TAG}"
  podman push backend "${REPOSITORY}/backend:${now}"
fi

if [ "$SKIP_FRONTEND" != 1 ] ;then
  podman build -f frontend/frontend.containerfile --tag frontend
  podman push frontend "${REPOSITORY}/frontend:${TAG}"
  podman push frontend "${REPOSITORY}/frontend:${now}"
fi
