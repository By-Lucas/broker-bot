from django.urls import re_path
from .consumers import TradesConsumer



websocket_urlpatterns = [
    re_path(r'ws/trader/(?P<broker_name>\w+)/$', TradesConsumer.as_asgi()),
]
