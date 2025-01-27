import json
from redis import Redis
from typing import Any, Awaitable, Union
from redis.exceptions import RedisError, ResponseError, TimeoutError, ClusterError


class RedisCache:
    def __init__(self, host:str = "localhost", port:int = 6379, db:int = 0) -> None:
        """Iniciar a Classe Cache Redis"""
        self.redis = Redis(host=host, port=port, db=db)

    def add_cache(self, name:str, value, expire:int=3600) -> Union[Awaitable, Any]:
        """ Função adicionar dados de registro no Redis e
            definir o tempo de expiração para chave 
            expire = seconds (3600)"""
        #days = datetime.timedelta(days=7)
        #seconds = days.total_seconds()
        value_json = json.dumps(value)
        self.redis.set(name, value_json)
        self.redis.expire(name, time=expire)
        print('Registro adicionado a cache redis')

    def get_cache(self, name:str) -> dict:
        """ Função obter dados de registro no Redis."""
        value = self.redis.get(name)
        if value:
            print("pegando dados do redis")
            value = json.loads(value)
        return value
    
    def add_news_to_cache(self, news_id, subject):
        """Adicionar notícia ao cache com a data de publicação"""
        value = f'{news_id}-{subject}'  # Salvar a data de publicação como timestamp
        self.redis.set(value, subject)
        hour_24 = 86400
        hour_28 = 100800 
        self.redis.expire(value, time=hour_28)
        print(f"Notícia {news_id} adicionada ao cache com assunto da publicação {subject}")
    
    def is_news_sent_recently(self, news_id, subject):
        value = str(f'{news_id}-{subject}')
        """Verificar se a notícia foi enviada recentemente (dentro do período de 28 horas)"""
        data = self.redis.get(value)
        if data and data.decode('utf-8') == subject:
            return True
        return False
    
    def delete_news_registry(self, news_id, subject) -> Union[Awaitable, Any]:
        """ Função para excluir dados do registro no Redis."""
        value = str(f'{news_id}-{subject}')
        self.redis.delete(value)
        print('Registro em cache deletado')

    def registry_exists(self, name:str) -> Union[Awaitable, Any]:
        """ Função para verificar se existem dados de registro no Redis."""
        exists = self.redis.exists(name)
        return exists

    def delete_registry(self, name:str) -> Union[Awaitable, Any]:
        """ Função para excluir dados do registro no Redis."""
        self.redis.delete(name)
        print('Registro em cache deletado')
