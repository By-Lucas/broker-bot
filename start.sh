#!/bin/bash

# Purga as filas do Celery
echo "Purging Celery tasks..."
celery -A broker_bot purge -f

# Inicializa o Celery Worker no background
echo "Starting Celery worker..."
celery -A broker_bot worker --time-limit 14400 -c 4 --without-heartbeat --hostname worker@%h --loglevel INFO &
celery -A broker_bot beat --loglevel INFO &

# Aguarda alguns segundos para garantir que os serviços Celery estão estáveis
sleep 5

# Coleta arquivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Aplica as migrações (descomente se necessário)
echo "Applying database makemigrations and migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput


# Inicia o servidor Django com Daphne
echo "Starting server with Daphne..."
exec daphne -b 0.0.0.0 -p 8000 broker_bot.asgi:application
