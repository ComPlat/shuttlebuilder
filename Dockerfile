FROM python:3.12
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
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

ARG SUPERUSER_NAME
ARG SUPERUSER_EMAIL
ARG SUPERUSER_PASS

COPY . .

COPY etc_config/default.conf /etc/nginx/sites-enabled/default
COPY www /usr/share/nginx/static
# COPY media /usr/share/nginx/media

EXPOSE 80

#CMD python ./manage.py runserver 0.0.0.0:8000
CMD service nginx start && ./manage.py migrate && ./manage.py initsuperuser && daphne -b 0.0.0.0 -p 8000 ShuttleBuilder.asgi:application