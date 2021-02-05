FROM quay.io/fedora/fedora:34

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN mkdir /backend

COPY app/ /backend/app
COPY scripts/ /backend/scripts
COPY requirements.txt /backend

WORKDIR /backend

RUN ln -s /usr/bin/python3 /usr/bin/python \
  && dnf install -y python3-pip \
  && pip install --no-cache-dir -r requirements.txt

CMD ["/usr/bin/bash", "./scripts/start.sh"]


