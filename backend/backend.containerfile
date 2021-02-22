FROM docker.io/library/python:3.9.1-buster

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN mkdir /backend

COPY app/ /backend/app
COPY scripts/ /backend/scripts
COPY requirements.txt /backend

WORKDIR /backend

EXPOSE 8000
RUN pip install --no-cache-dir -r requirements.txt

CMD ["/bin/sh", "./scripts/start.sh"]


