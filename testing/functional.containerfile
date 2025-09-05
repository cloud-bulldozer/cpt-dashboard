FROM quay.io/centos/centos:stream10

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

RUN dnf install -y pip gcc python3-devel gcc-c++

RUN pip install --user poetry

# 3) Copy manifest files & install Python deps via export
COPY backend/pyproject.toml backend/poetry.lock backend/version.json ./
RUN poetry install --no-root --no-interaction --no-ansi && \
    # Ensure generated cache and config files are group-writable
    # for both OpenShift (random UID in GID=0) and Podman (root) 
    # environments
    chmod -R g+rwX ${HOME}/.cache/pypoetry ${HOME}/.config/pypoetry

ENV SERVER=http://localhost:8000

ENTRYPOINT ["poetry", "run", "pytest", "-s", "tests/functional"]
