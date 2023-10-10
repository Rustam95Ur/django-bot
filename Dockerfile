FROM python:3.10-slim
ARG DJANGO_ENV

ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.4.2 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

RUN apt-get update && \
  apt-get install --no-install-recommends -y \
  curl libpq-dev wget  wget build-essential libncursesw5-dev libssl-dev \
     libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev python3-dev\
  gettext \
  # Cleaning cache:
  && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
  # Installing `poetry` package manager:
  # https://github.com/python-poetry/poetry
  && pip install idna "poetry==$POETRY_VERSION" && poetry --version

RUN mkdir -p /opt/services/app/src
WORKDIR /opt/services/app/src

COPY ./poetry.lock ./pyproject.toml /opt/services/app/src/

# Project initialization:
RUN echo "$DJANGO_ENV" \
  && poetry install \
  $(if [ "$DJANGO_ENV" = 'Production' ]; then echo '--no-dev'; fi) \
  --no-interaction --no-ansi \
  # Cleaning poetry installation's cache for production:
  && if [ "$DJANGO_ENV" = 'Production' ]; then rm -rf "$POETRY_CACHE_DIR"; fi

COPY . /opt/services/app/src