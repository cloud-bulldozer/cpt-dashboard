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

RUN dnf install -y pip gcc python3-devel gcc-c++

RUN pip install --user poetry && \
    poetry self add poetry-plugin-export && \
    poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    pip install -U typing-extensions && \
    pip install --user dash && \
    pip install --no-cache-dir -r requirements.txt

ENV SERVER=http://localhost:8000

ENTRYPOINT ["pytest", "-s", "tests/functional"]
