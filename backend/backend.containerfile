FROM quay.io/centos/centos:stream9

# 0) Configure Poetry and environment for OpenShift non-root execution
ENV POETRY_VIRTUALENVS_CREATE=false \
    HOME=/opt/backend \
    XDG_CONFIG_HOME=/opt/backend/.config \
    XDG_CACHE_HOME=/opt/backend/.cache

# 1) Install system deps + Poetry globally (root)
#    Installing Poetry globally ensures the binary is on /usr/local/bin
#    and therefore available in both OpenShift (random UID) and Podman (root) environments
RUN dnf install -y python3-pip gcc python3-devel gcc-c++ && \
    pip3 install --no-cache-dir poetry && \
    poetry self add poetry-plugin-export && \
    dnf clean all

# 2) Prepare writable dirs
#    Grant group rwx so both OpenShift’s random non-root UID (in GID=0) and
#    Podman's default user, root, can write
RUN mkdir -p /opt/backend /opt/backend/.config/pypoetry /opt/backend/.cache/pypoetry && \
    chmod -R g+rwX /opt/backend

WORKDIR /opt/backend

# 3) Copy manifest files & install Python deps via export
COPY pyproject.toml poetry.lock version.json ./
RUN poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    pip3 install --no-cache-dir -r requirements.txt && \
    # Ensure generated cache and config files are group-writable
    # for both OpenShift (random UID in GID=0) and Podman (root) 
    # environments
    chmod -R g+rwX /opt/backend/.cache/pypoetry /opt/backend/.config/pypoetry

COPY app/     ./app
COPY scripts/ ./scripts

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "scripts/start.sh"]
