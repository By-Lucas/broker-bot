FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Define o diretório de trabalho padrão
WORKDIR /app

# Instalar dependências necessárias, incluindo libpq-dev para pg_config
RUN apt update && apt upgrade -y \
    && apt install -y --no-install-recommends \
    git \
    openssh-client \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    netcat \
    && rm -rf /var/lib/apt/lists/*


RUN python -m pip install --upgrade pip

# Atualize setuptools para evitar problemas com pkg_resources
RUN pip install --upgrade setuptools

# Adiciona os requisitos do projeto
COPY requirements.txt .

# Adiciona os requisitos de desenvolvimento do projeto, se necessário
COPY requirements-dev.txt .

# Instala os pacotes listados em requirements.txt
RUN pip3 --disable-pip-version-check --no-cache-dir install -r requirements.txt \
    && rm -rf requirements.txt
        
# Atualize setuptools para evitar problemas com pkg_resources
RUN pip install --upgrade setuptools


# Copia todo o código da aplicação para o diretório de trabalho
COPY . .

# Copia o start de inicialização para o diretório de trabalho
COPY start.sh ./start.sh


# Dá permissão de execução ao script de inicialização
RUN chmod +x start.sh

# Exponha a porta que o servidor Django irá usar
EXPOSE 8000

# Comando para iniciar o aplicativo usando o script start.sh
CMD ["./start.sh"]