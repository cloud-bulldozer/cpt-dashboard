FROM quay.io/centos/centos:stream9

# 0) Configure Poetry and environment for OpenShift non-root execution
ENV POETRY_VIRTUALENVS_CREATE=false \
    HOME=/backend \
    XDG_CONFIG_HOME=/backend/.config \
    XDG_CACHE_HOME=/backend/.cache

RUN dnf update -y
RUN dnf install -y 'dnf-command(config-manager)'
RUN dnf config-manager --set-enabled crb
RUN dnf install -y epel-release epel-next-release
RUN dnf install -y python3.12 python3.12-devel python3.12-pip gcc gcc-c++

RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && ln -sf /usr/bin/pip3.12 /usr/bin/pip3

# 1) Install system deps + Poetry globally (root)
#    Installing Poetry globally ensures the binary is on /usr/local/bin
#    and therefore available in both OpenShift (random UID) and Podman (root) environments
RUN pip3 install --no-cache-dir poetry && \
    dnf clean all

# 2) Prepare writable dirs
#    Grant group rwx so both OpenShift’s random non-root UID (in GID=0) and
#    Podman's default user, root, can write
RUN mkdir -p ${HOME} ${HOME}/.config/pypoetry ${HOME}/.cache/pypoetry && \
    chmod -R g+rwX ${HOME}

WORKDIR ${HOME}

# 3) Copy manifest files & install Python deps
COPY pyproject.toml poetry.lock version.json ./

# Add verbose output for debugging the GitHub Action build failure
# (Just in case that helps...)
RUN poetry install -vvv --no-root --no-interaction --no-ansi
# Ensure generated cache and config files are group-writable
# for both OpenShift (random UID in GID=0) and Podman (root) 
# environments
RUN chmod -R g+rwX ${HOME}/.cache/pypoetry ${HOME}/.config/pypoetry

COPY app/     ./app
COPY scripts/ ./scripts

# separate installation for project source code as a package
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "scripts/start.sh"]
