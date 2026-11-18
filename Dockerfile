FROM python:3.14-slim AS client_build
RUN apt-get update

ENV NODE_VERSION=22.16.0
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version

RUN mkdir -p /srv/app
WORKDIR /srv/app

COPY . .

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry install --no-root
RUN poetry self add poetry-plugin-export
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt

# RUN pip install --no-cache-dir -r requirements.txt

RUN npm install

RUN poetry run python manage.py sdc_update_links
RUN npm run build
RUN poetry run python manage.py collectstatic  --no-input

FROM python:3.14-slim AS shuttlebuilder
LABEL authors="martin"
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /srv/app
RUN mkdir -p /srv/app/private_libs
WORKDIR /srv/app
RUN apt-get update && apt-get --assume-yes upgrade && apt-get install -y git nginx nodejs npm zip gzip tar wget libmagic1

# Go toolchains. Both tarballs are SHA256-pinned.
# To bump modern Go: take the new version and the linux-amd64 sha256 from
# https://go.dev/dl/?mode=json and change GO_VERSION and GO_SHA256 below.
# Go 1.10.8 (Windows XP, GOPATH mode) is not on PATH; it is used via XP_GOROOT.
# GOWEBDAV_REV must follow the gowebdav pin in Shuttle's go.mod
# (v0.0.0-20220901075112-8721ee532c0c -> 8721ee532c0c).
WORKDIR /opt
ARG GO_VERSION=1.26.11
ARG GO_SHA256=9849f4e04ee35303714e34fbc3ac8ab44ea3e448a95aa182f91e3b9b79c710ec
RUN set -e \
    && wget -q -O "go${GO_VERSION}.linux-amd64.tar.gz" "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" \
    && echo "${GO_SHA256}  go${GO_VERSION}.linux-amd64.tar.gz" | sha256sum -c - \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz" \
    && rm "go${GO_VERSION}.linux-amd64.tar.gz"

ARG XP_GO_VERSION=1.10.8
ARG XP_GO_SHA256=d8626fb6f9a3ab397d88c483b576be41fa81eefcec2fd18562c87626dbb3c39e
RUN set -e \
    && wget -q -O "go${XP_GO_VERSION}.linux-amd64.tar.gz" "https://go.dev/dl/go${XP_GO_VERSION}.linux-amd64.tar.gz" \
    && echo "${XP_GO_SHA256}  go${XP_GO_VERSION}.linux-amd64.tar.gz" | sha256sum -c - \
    && rm -rf "/usr/local/go${XP_GO_VERSION}" \
    && mkdir -p "/usr/local/go${XP_GO_VERSION}" \
    && tar -C "/usr/local/go${XP_GO_VERSION}" --strip-components=1 -xzf "go${XP_GO_VERSION}.linux-amd64.tar.gz" \
    && rm "go${XP_GO_VERSION}.linux-amd64.tar.gz"

RUN mkdir -p /usr/local/gopath

ENV GOROOT="/usr/local/go"
ENV GOPATH="/usr/local/gopath"
ENV XP_GOROOT="/usr/local/go1.10.8"
ENV GOTOOLCHAIN=local

ENV PATH="${PATH}:${GOPATH}/bin:${GOROOT}/bin"

ARG GOWEBDAV_REV=8721ee532c0c
RUN set -e \
    && GOROOT="$XP_GOROOT" "$XP_GOROOT/bin/go" get -d github.com/StarmanMartin/gowebdav \
    && git -C "$GOPATH/src/github.com/StarmanMartin/gowebdav" checkout --quiet "$GOWEBDAV_REV"

COPY . .

# install dependencies
COPY --from=client_build /srv/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

ARG SUPERUSER_NAME
ARG SUPERUSER_EMAIL
ARG SUPERUSER_PASS



COPY etc_config/default.conf /etc/nginx/sites-enabled/default
COPY --from=client_build /srv/app/www /usr/share/nginx/static
# COPY media /usr/share/nginx/media

EXPOSE 80

RUN mv ./etc_config/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh



#CMD python ./manage.py runserver 0.0.0.0:8000
ENTRYPOINT ./entrypoint.sh