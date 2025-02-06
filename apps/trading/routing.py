from django.urls import re_path

from notification.consumers import NotificationConsumer
from .consumers import TradesConsumer



websocket_urlpatterns = [
    re_path(r'ws/trader/(?P<broker_name>\w+)/$', TradesConsumer.as_asgi()),
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
]
