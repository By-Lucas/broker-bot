instalar requirements-dev.txt
```
pip install -r requirements-dev.txt --root-user-action=ignore
```


```
daphne -b 0.0.0.0 -p 8000 broker_bot.asgi:application
```
