import json
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from trading.utils import CustomJSONEncoder
from bots.constants import CUSTOM_PARITIES

from .utils import parse_time_aware
from trading.models import TradeOrder
from integrations.models import Quotex
from trading.services import get_detailed_dashboard_data


def create_trade_order_sync(status_buy, asset, info_buy, data={}):
    """ Cria ou atualiza um trade e notifica o WebSocket. """

    broker_obj = Quotex.objects.get(trader_id=info_buy.get("uid"))

    order_type = "BUY"  # Pode ser ajustado conforme necessário
    open_time = parse_time_aware(info_buy.get("openTime"))
    close_time = parse_time_aware(info_buy.get("closeTime"))

    trade_order, created = TradeOrder.objects.update_or_create(
        broker=broker_obj,  # FK direto para a corretora Quotex
        id_trade=info_buy.get("id"),  # ID único da operação na corretora
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

    # ✅ Se o trade foi criado ou atualizado, dispara a atualização via WebSocket corretamente
    if created or trade_order:
        send_trade_update(trade_order.broker, trade_order.broker.customer) # ✅ Correto

    return trade_order


def send_trade_update(broker, user):
    """ Envia os dados do usuário autenticado para o WebSocket """
    try:
        channel_layer = get_channel_layer()

        # ✅ Obtém os dados filtrados pelo usuário (cotação e saldo incluídos)
        dashboard_data = asyncio.run(get_detailed_dashboard_data(broker, user))

        json_data = json.dumps(dashboard_data, cls=CustomJSONEncoder)

        async_to_sync(channel_layer.group_send)(
            f"bot_control",
            {
                "type": "send_trades_update",
                "data": json_data,
            }
        )

        print(f"🚀 Dados enviados com sucesso para o WebSocket! ({broker.customer.email})")

    except Exception as e:
        print(f"⚠️ Erro ao enviar dados via WebSocket: {e}")
