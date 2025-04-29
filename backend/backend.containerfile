FROM quay.io/centos/centos:stream9

# 0) Configure Poetry and environment for OpenShift non-root execution
ENV POETRY_VIRTUALENVS_CREATE=false \
    HOME=/opt/backend \
    XDG_CONFIG_HOME=/opt/backend/.config \
    XDG_CACHE_HOME=/opt/backend/.cache

# 1) Install system deps + Poetry globally (root)
RUN dnf install -y python3-pip gcc python3-devel gcc-c++ && \
    pip3 install --no-cache-dir poetry && \
    poetry self add poetry-plugin-export && \
    dnf clean all

# 2) Prepare world-writable dirs (for arbitrary UID)
RUN mkdir -p /opt/backend && \
    mkdir -p /opt/backend/.config/pypoetry && \
    mkdir -p /opt/backend/.cache/pypoetry && \
    chmod -R g+rwX /opt/backend

WORKDIR /opt/backend
EXPOSE 8000

# 3) Copy manifest files & install Python deps
COPY pyproject.toml poetry.lock version.json ./
RUN poetry config virtualenvs.in-project true && \
    poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    pip3 install --no-cache-dir -r requirements.txt && \
    chmod -R g+rwX /opt/backend/.cache/pypoetry && \
    chmod -R g+rwX /opt/backend/.config/pypoetry

# 4) Copy application code and scripts
COPY app/     ./app
COPY scripts/ ./scripts

# 5) Launch via your startup script
ENTRYPOINT ["/bin/bash", "scripts/start.sh"]
