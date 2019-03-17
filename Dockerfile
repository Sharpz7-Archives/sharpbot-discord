FROM python:3.7.2-slim-stretch

RUN apt update -y
RUN apt install -y git

RUN pip install pipenv
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --system

WORKDIR /project

CMD ["python", "-u", "run.py"]

