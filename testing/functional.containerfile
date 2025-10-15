FROM quay.io/centos/centos:stream9

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN mkdir -p /backend/tests/functional

COPY backend/tests/functional/*.py /backend/tests/functional/
COPY backend/pyproject.toml /backend
COPY backend/poetry.lock /backend
COPY testing/db_seed.py /backend

WORKDIR /backend

RUN mkdir -p ${HOME} ${HOME}/.config/pypoetry ${HOME}/.cache/pypoetry && \
    chmod -R g+rwX ${HOME}

RUN dnf update -y
RUN dnf install -y 'dnf-command(config-manager)'
RUN dnf config-manager --set-enabled crb
RUN dnf install -y epel-release epel-next-release
RUN dnf install -y python3.12 python3.12-devel python3.12-pip gcc gcc-c++

RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && ln -sf /usr/bin/pip3.12 /usr/bin/pip3

RUN pip3 install --user poetry

# 3) Copy manifest files & install Python deps via export
COPY backend/pyproject.toml backend/poetry.lock backend/version.json ./
RUN poetry install --no-root --no-interaction --no-ansi && \
    # Ensure generated cache and config files are group-writable
    # for both OpenShift (random UID in GID=0) and Podman (root) 
    # environments
    chmod -R g+rwX ${HOME}/.cache/pypoetry ${HOME}/.config/pypoetry

ENV SERVER=http://localhost:8000

ENTRYPOINT ["poetry", "run", "pytest", "-s", "tests/functional"]
