FROM python:3.7-slim-buster

LABEL maintainer="vqcuong96@gmail.com"

ENV container=docker

ADD requirements.txt /tmp

ENV EXPORTER_PORT=9123 \
    EXPORTER_HOME=/exporter \
    EXPORTER_METRICS_DIR=/exporter/metrics \
    EXPORTER_LOGS_DIR=/exporter/logs

RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends net-tools dos2unix dumb-init -y \
    && pip install -r /tmp/requirements.txt \
    && mkdir -p ${EXPORTER_HOME} ${EXPORTER_LOGS_DIR} \
    && rm -rf /tmp/* \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && apt-get autoremove -yqq --purge \
    && apt-get clean

ADD hadoop_exporter /exporter/hadoop_exporter
ADD metrics /exporter/metrics
ADD service.py /service.py
ADD entrypoint.sh /entrypoint.sh

RUN set -ex \
    && chmod +x /entrypoint.sh /service.py

ENV PYTHONPATH=${PYTHONPATH}:${EXPORTER_HOME}
EXPOSE ${EXPORTER_PORT}
ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint.sh"]
