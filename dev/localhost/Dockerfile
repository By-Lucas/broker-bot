FROM mcr.microsoft.com/devcontainers/python:1-3.10-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1


RUN python -m pip install --upgrade pip

# Atualize setuptools para evitar problemas com pkg_resources
RUN pip install --upgrade setuptools


# Adiciona os requisitos do projeto
COPY requirements.txt /tmp/pip-tmp/requirements.txt

# Adiciona os requisitos de desenvolvimento do projeto, se necessário
COPY requirements-dev.txt /tmp/pip-tmp/requirements-dev.txt

# Instala os pacotes listados em requirements.txt
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp/requirements.txt

# Instala os pacotes listados em requirements-dev.txt, se o arquivo existir
RUN if [ -f /tmp/pip-tmp/requirements-dev.txt ]; then pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements-dev.txt \
    && rm -rf /tmp/pip-tmp/requirements-dev.txt; fi

# [Opcional] Descomente esta seção para instalar pacotes adicionais do sistema operacional.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <sua-lista-de-pacotes-aqui>