import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from bots.utils import parse_time_aware
from trading.utils import CustomJSONEncoder
from trading.models import TradeOrder
from integrations.models import Quotex
from trading.services import get_detailed_dashboard_data


def create_trade_order_sync(status_buy, asset, info_buy, data={}):
    """ Cria ou atualiza um trade e notifica o WebSocket. """

    broker_obj = Quotex.objects.get(trader_id=info_buy.get("uid"))

    order_type = "BUY"
    open_time = parse_time_aware(info_buy.get("openTime"))
    close_time = parse_time_aware(info_buy.get("closeTime"))

    trade_order, created = TradeOrder.objects.update_or_create(
        broker=broker_obj,  
        id_trade=info_buy.get("id"),  
        defaults={
            "order_type": order_type,
            "amount": info_buy["amount"],
            "asset_order": asset,
            "status": "EXECUTED" if status_buy else "FAILED",
            "uid": info_buy.get("uid"),
            "percent_profit": info_buy.get("percentProfit"),
            "open_time": open_time,
            "close_time": close_time,
            "request_id": info_buy.get("requestId"),
            "result": 0,
            "request_body": info_buy,
        }
    )

    if created or trade_order:
        send_trade_update(trade_order.broker)

    return trade_order


def send_trade_update(broker, broker_slug="quotex"):
    """ Aciona a função `send_websocket_user` no WebSocket sem enviar dados extras """

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'bot_trades_{broker_slug}',
        {
            'type': 'send_websocket_user',
            "action": "update",
            "data": {},
        }
    )

    print(f"🚀 Comando enviado ao WebSocket para {broker.customer.email if broker.customer else 'usuário desconhecido'}")