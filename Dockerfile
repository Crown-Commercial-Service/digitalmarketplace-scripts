FROM python:3.6.1-slim

ENV APP_DIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    gcc g++ make git libffi-dev libssl-dev libc6-dev

WORKDIR ${APP_DIR}

COPY requirements.txt ${APP_DIR}
RUN pip install --no-cache-dir -r requirements.txt

COPY . ${APP_DIR}

ARG release_name
RUN echo ${release_name} > ${APP_DIR}/version_label

CMD python --version && echo "Release: $(cat ${APP_DIR}/version_label)" && \
    echo "Available scripts:" && find scripts -type f | sort
