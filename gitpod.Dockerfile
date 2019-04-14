FROM python:3.7.3-slim-stretch

RUN apt install wget procps libcurl3 libprotobuf10 -y
RUN wget "https://github.com/srh/rethinkdb/releases/download/v2.3.6.srh.1/rethinkdb_2.3.6.srh.1.0stretch_amd64.deb"
RUN dpkg -i rethinkdb_2.3.6.srh.1.0stretch_amd64.deb
RUN rethinkdb -n pdrdb -d /data --bind 0.0.0.0 --server-tag default --http-port 28010 --driver-port 28015

RUN pip install pipenv
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --system