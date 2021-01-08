# ocp_perf_dashboard
OpenShift Container Platform Performance Dashboard


## Example Container Orchestration

This will build and run the backend and frontend containers, and expose their pod on port `8080`.

### Requires

* podman
* working direcotry is the repository root directory

```shell 
#!/bin/sh

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
```