from django.contrib.contenttypes.models import ContentType

from .utils import parse_time_aware
from trading.models import TradeOrder
from integrations.models import Quotex  # Supondo que você queira referenciar Quotex



def create_trade_order_sync(status_buy, asset, info_buy, data={}):
    broker_obj = Quotex.objects.get(trader_id=info_buy.get("uid"))
    content_type = ContentType.objects.get_for_model(Quotex)

    order_type = "BUY"# if data["direction"].upper() == "CALL" else "SELL"

    open_time = parse_time_aware(info_buy.get("openTime"))  # Ex.: parse_time é uma função util
    close_time = parse_time_aware(info_buy.get("closeTime"))

    trade_order, created = TradeOrder.objects.update_or_create(
        content_type=content_type,
        object_id=broker_obj.id,
        id_trade=info_buy.get("id"),  # ID da Operação é a chave para evitar duplicação
        defaults={
            "broker": broker_obj,
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
    return trade_order or created

