FROM python:3.12 AS client_build
RUN apt-get update

ENV NODE_VERSION=22.8.0
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

RUN poetry install
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN npm install

RUN python manage.py sdc_update_links
RUN npm run build
RUN python manage.py collectstatic  --no-input

FROM python:3.12 AS shuttlebuilder
LABEL authors="martin"
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /srv/app
RUN mkdir -p /srv/app/private_libs
WORKDIR /srv/app
RUN apt-get update && apt-get --assume-yes upgrade && apt-get install -y git nginx nodejs npm zip gzip tar

WORKDIR /opt
RUN wget "https://go.dev/dl/go1.19.3.linux-amd64.tar.gz"
RUN rm -rf /usr/local/go
RUN tar -C /usr/local -xzf go1.19.3.linux-amd64.tar.gz
RUN mkdir "/usr/local/gopath"

ENV GOROOT="/usr/local/go"
ENV GOPATH="/usr/local/gopath"

ENV PATH="${PATH}:${GOPATH}/bin:${GOROOT}/bin"

RUN go install golang.org/dl/go1.10@latest
RUN go1.10 download
RUN go1.10 get github.com/StarmanMartin/gowebdav

# install dependencies
COPY --from=client_build /srv/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

ARG SUPERUSER_NAME
ARG SUPERUSER_EMAIL
ARG SUPERUSER_PASS

COPY . .

COPY etc_config/default.conf /etc/nginx/sites-enabled/default
COPY --from=client_build /srv/app/www /usr/share/nginx/static
# COPY media /usr/share/nginx/media

EXPOSE 80

#CMD python ./manage.py runserver 0.0.0.0:8000
CMD service nginx start && ./manage.py migrate && ./manage.py initsuperuser && daphne -b 0.0.0.0 -p 8000 ShuttleBuilder.asgi:application