FROM python:3.5

ENV LANG C.UTF-8
ENV SHELL bash

RUN pip3 install pipenv

WORKDIR /code

ADD ./Pipfile /code
ADD ./Pipfile.lock /code

RUN pipenv install --dev

ADD . /code


ENTRYPOINT [ "pipenv", "run" ]
