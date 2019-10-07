FROM python:3.7.3-slim-stretch

RUN pip install pipenv
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --system

COPY ./project /project

WORKDIR /project

CMD ["python", "-u", "run.py"]

