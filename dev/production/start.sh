#!/bin/sh

# REMOVER ApiBuilderKit e clonar novamente
# fuser -k APIBuilderKit || true

# # Verificar se o diretório APIBuilderKit já existe e tentar remover
# if [ -d "APIBuilderKit" ]; then
#     echo "Tentando remover o diretório APIBuilderKit existente..."
#     rm -rf APIBuilderKit || { echo "Falha ao remover o diretório APIBuilderKit." >&2; exit 1; }
# fi

# # Adiciona a chave privada ao agente ssh
# eval "$(ssh-agent -s)" \
#     && ssh-add /root/.ssh/id_rsa

# # Clonar o repositório
# git clone git@github.com:By-Lucas/APIBuilderKit.git APIBuilderKit || { echo "Falha ao clonar o repositório APIBuilderKit." >&2; exit 1; }

# Iniciar workers do Celery
celery -A tknexus worker --time-limit 14400 -c 2 --without-heartbeat --hostname worker@%h --loglevel INFO --detach &

# Para tarefas medianas
#celery -A tknexus worker --time-limit 14400 -c 6 -Q tknexus-medians --without-heartbeat --hostname worker-medians@%h --loglevel INFO &

# Para tarefas mais pesadas e complexas
#celery -A tknexus worker --time-limit 14400 -c 8 -Q tknexus-complex --without-heartbeat --hostname worker-complex@%h --loglevel INFO &


celery -A tknexus beat --loglevel INFO --detach &

# Esperar que todos os processos em segundo plano sejam iniciados
sleep 5

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Executar migrações e iniciar o servidor Django
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Iniciar o Gunicorn
gunicorn tknexus.wsgi:application --bind 0.0.0.0:$PORT


