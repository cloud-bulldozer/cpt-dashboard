FROM docker.io/library/python:3.9.4

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN mkdir /backend

COPY app/ /backend/app
COPY scripts/ /backend/scripts
COPY pyproject.toml /backend
COPY poetry.lock /backend

WORKDIR /backend

EXPOSE 8000

RUN pip install --user poetry && \
    poetry export -f requirements.txt -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash", "./scripts/start.sh"]


