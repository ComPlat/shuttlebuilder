FROM python:3.13-slim
LABEL authors="martin"
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /srv/app
RUN apt-get update && apt-get --assume-yes upgrade

WORKDIR /srv/app


COPY ./ShuttleBuilder/brodcast_service_info.py .

RUN pip install --upgrade pip
RUN pip install "zeroconf==0.149.16"

CMD python ./brodcast_service_info.py