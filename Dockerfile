FROM python:3.6-slim

RUN wget --quiet -O /usr/local/bin/aws-auth https://raw.githubusercontent.com/alphagov/aws-auth/1741ad8b8454f54dd40fb730645fc2d6e3ed9ea9/aws-auth.sh \
    && chmod 0755 /usr/local/bin/aws-auth

RUN wget --quiet -O /usr/local/bin/sops https://github.com/mozilla/sops/releases/download/3.2.0/sops-3.2.0.linux \
    && echo 'fec5b5b5bbae922a829a6277f6d66a061d990c04132da3c82db32ccc309a22e7  /usr/local/bin/sops' | sha256sum -c - \
    && chmod 0755 /usr/local/bin/sops

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ make git libffi-dev libssl-dev libc6-dev wget curl socat jq

ENV APP_DIR /app
WORKDIR ${APP_DIR}

COPY requirements.txt ${APP_DIR}
RUN pip install --no-cache-dir -r requirements.txt

COPY . ${APP_DIR}
RUN mv docker_for_mac_entrypoint.sh /usr/local/bin

ARG release_name
RUN echo ${release_name} > ${APP_DIR}/version_label

CMD python --version && echo "Release: $(cat ${APP_DIR}/version_label)" && \
    echo "Available scripts:" && find scripts -type f | sort
