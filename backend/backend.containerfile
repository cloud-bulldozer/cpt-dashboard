FROM quay.io/centos/centos:stream9

ENV PATH=/root/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend \
    PATH=/usr/local/bin:$PATH 


RUN useradd -m -d /home/appuser appuser && \
    chmod 755 /home/appuser && \
    mkdir /home/appuser/backend && \
    chown appuser:appuser /home/appuser/backend && \
    chmod 777 /home/appuser/backend



COPY app/ /home/appuser/backend/app
COPY scripts/ /home/appuser/backend/scripts
COPY pyproject.toml /home/appuser/backend
COPY poetry.lock /home/appuser/backend


WORKDIR /home/appuser/backend

EXPOSE 8000

RUN dnf install -y pip gcc python3-devel gcc-c++ git

RUN pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry self add poetry-plugin-export && \
    poetry export --without-hashes -f requirements.txt -o requirements.txt && \
    pip install -U typing-extensions && \
    pip install --user dash && \
    pip install --no-cache-dir -r requirements.txt 

COPY version.json version.json

WORKDIR /home/appuser/backend

ENTRYPOINT ["/bin/bash", "./scripts/start.sh"]
