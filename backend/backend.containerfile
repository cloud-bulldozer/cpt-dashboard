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
    dnf clean all

# 2) Prepare writable dirs
#    Grant group rwx so both OpenShift’s random non-root UID (in GID=0) and
#    Podman's default user, root, can write
RUN mkdir -p ${HOME} ${HOME}/.config/pypoetry ${HOME}/.cache/pypoetry && \
    chmod -R g+rwX ${HOME}

WORKDIR ${HOME}

# 3) Copy manifest files & install Python deps via export
COPY pyproject.toml poetry.lock version.json ./
RUN poetry install --no-root --no-interaction --no-ansi && \
    # Ensure generated cache and config files are group-writable
    # for both OpenShift (random UID in GID=0) and Podman (root) 
    # environments
    chmod -R g+rwX ${HOME}/.cache/pypoetry ${HOME}/.config/pypoetry

COPY app/     ./app
COPY scripts/ ./scripts

# separate installation for project source code as a package
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "scripts/start.sh"]
