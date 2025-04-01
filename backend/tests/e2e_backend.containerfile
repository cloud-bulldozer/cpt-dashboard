FROM quay.io/centos/centos:stream9

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN dnf install -y pip gcc python3-devel gcc-c++

RUN mkdir -p /backend/tests

COPY pyproject.toml /backend/pyproject.toml
COPY poetry.lock /backend/poetry.lock
COPY app/ /backend/app/
COPY tests/ /backend/tests/

RUN cd /backend && \
    pip install --user poetry && \
    poetry install    

COPY scripts/ /backend/scripts/
COPY ocpperf_test.toml /backend/ocpperf.toml
COPY ocpperf_test.toml /backend/ocpperf_test.toml

WORKDIR /backend

ENV SERVER=http://localhost:8000

EXPOSE 8000

CMD ["/bin/bash", "./scripts/start.sh"]
