#!/bin/bash

cd backend
pipenv lock -r > requirements.txt
podman build . --tag ocpp-back-i

cd ../frontend
podman build . --tag ocpp-front-i


podman rm -f front back
podman pod rm -f ocpp
podman pod create --name ocpp --publish 8080:80

podman run -d --name=back --pod ocpp ocpp-back-i
podman run -d --name=front --pod ocpp ocpp-front-i