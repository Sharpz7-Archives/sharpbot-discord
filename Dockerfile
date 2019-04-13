FROM python:3.7.2-slim-stretch

RUN pip install pipenv
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --system

WORKDIR /project

CMD ["python", "-u", "run.py"]

