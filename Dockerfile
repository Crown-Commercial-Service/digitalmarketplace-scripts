FROM python:3.13.0b2-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ make git libffi-dev libssl-dev libc6-dev wget curl socat jq

RUN wget --quiet -O /usr/local/bin/aws-auth https://raw.githubusercontent.com/alphagov/aws-auth/1741ad8b8454f54dd40fb730645fc2d6e3ed9ea9/aws-auth.sh \
    && chmod 0755 /usr/local/bin/aws-auth

RUN wget --quiet -O /usr/local/bin/sops https://github.com/mozilla/sops/releases/download/3.2.0/sops-3.2.0.linux \
    && echo 'fec5b5b5bbae922a829a6277f6d66a061d990c04132da3c82db32ccc309a22e7  /usr/local/bin/sops' | sha256sum -c - \
    && chmod 0755 /usr/local/bin/sops

RUN wget --quiet -O /usr/local/bin/docopts https://github.com/docopt/docopts/releases/download/v0.6.3-alpha1/docopts \
    && echo '45812802bef1d91d5a431c11415839d4609aa2d82cde627fad844d24e7e265e7  /usr/local/bin/docopts' | sha256sum -c - \
    && chmod 0755 /usr/local/bin/docopts

RUN wget --quiet -O /usr/local/bin/docopts.sh https://raw.githubusercontent.com/docopt/docopts/1156d73a85d5ae4810b80908dbaa46ad9222dabd/docopts.sh \
    && echo 'd117d3290def71d6a7fdc5b67efddfc3a9299f146bb4f98f96e322222957d1ce /usr/local/bin/docopts.sh' | sha256sum -c - \
    && chmod 0755 /usr/local/bin/docopts.sh

RUN pip install --no-cache-dir --upgrade pip==21.0.1

ENV PATH "/root/.local/bin:$PATH"
RUN pip install --no-cache-dir pipx \
    && pipx install --pip-args="--no-cache-dir" awscli==1.19.5 \
    && pip uninstall -y pipx

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
