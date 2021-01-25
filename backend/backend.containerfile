FROM quay.io/fedora/fedora:34

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/

COPY app /app

WORKDIR /app

RUN ln -s /usr/bin/python3 /usr/bin/python \
  && dnf install -y python3-pip \
  && pip install --no-cache-dir -r requirements.txt

CMD ["/usr/bin/bash", "./scripts/start.sh"]


