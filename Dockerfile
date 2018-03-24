FROM python:3.6.1-slim

ENV APP_DIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ make git libffi-dev libssl-dev libc6-dev wget curl && \
    wget --quiet -O /usr/local/bin/sops https://s3-eu-west-1.amazonaws.com/digitalmarketplace-public/sops_linux_amd64 && chmod 0755 /usr/local/bin/sops && \
    wget --quiet -O /usr/local/bin/aws-auth https://raw.githubusercontent.com/alphagov/aws-auth/1741ad8b8454f54dd40fb730645fc2d6e3ed9ea9/aws-auth.sh && chmod 0755 /usr/local/bin/aws-auth && \
    wget --quiet -O /usr/local/bin/jq https://s3-eu-west-1.amazonaws.com/digitalmarketplace-public/jq-linux64 && chmod 0755 /usr/local/bin/jq

WORKDIR ${APP_DIR}

COPY requirements.txt ${APP_DIR}
RUN pip install --no-cache-dir -r requirements.txt

COPY . ${APP_DIR}

ARG release_name
RUN echo ${release_name} > ${APP_DIR}/version_label

CMD python --version && echo "Release: $(cat ${APP_DIR}/version_label)" && \
    echo "Available scripts:" && find scripts -type f | sort
