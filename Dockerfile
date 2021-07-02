FROM python:3.7
MAINTAINER vmizener

ENV PYTHONUNBUFFERED 1

COPY .flake8 /
COPY requirements.txt /
RUN pip install -r requirements.txt

RUN mkdir /app
COPY ./app /app
WORKDIR /app

RUN useradd -m user
USER user
