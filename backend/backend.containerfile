FROM quay.io/centos/centos:stream9

ENV HOME=/backend

ENV PATH=$HOME/.local/bin:$PATH \
    LANG=C.UTF-8 \
    PYTHONPATH=/backend

RUN mkdir /backend

COPY app/ /backend/app
COPY scripts/ /backend/scripts
COPY pyproject.toml /backend
COPY poetry.lock /backend

WORKDIR /backend

EXPOSE 8000

RUN dnf install -y pip gcc python3-devel gcc-c++

RUN pip install --user poetry && \
    poetry export -f requirements.txt -o requirements.txt && \
    pip install -U typing-extensions && \
    pip install --user dash && \
    pip install --no-cache-dir -r requirements.txt

RUN touch ocpperf.yaml && chmod 777 ocpperf.yaml
RUN chgrp -R 0 $HOME && chmod -R g=u $HOME

ENTRYPOINT ["/bin/bash", "./scripts/start.sh"]
