instalar requirements-dev.txt
```
pip install -r requirements-dev.txt --root-user-action=ignore
```


```
daphne -b 0.0.0.0 -p 8000 broker_bot.asgi:application
```


## COMANDOS PARA INSTALAR O REDIS E EXECUTAR
```
sudo apt update && sudo apt upgrade -y
sudo apt install redis-server -y
sudo service redis-server start
redis-cli ping
```