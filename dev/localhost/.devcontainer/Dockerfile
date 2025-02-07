# Use uma imagem base compatível
FROM mcr.microsoft.com/devcontainers/python:1-3.10-bookworm

# Variáveis de ambiente para otimizar o comportamento do Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

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
