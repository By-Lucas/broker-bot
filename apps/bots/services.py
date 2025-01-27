from django.contrib.contenttypes.models import ContentType

from .utils import parse_time_aware
from trading.models import TradeOrder
from integrations.models import Quotex  # Supondo que você queira referenciar Quotex



def create_trade_order_sync(status_buy, info_buy, data):
    broker_obj = Quotex.objects.get(id=data["broker_id"])
    content_type = ContentType.objects.get_for_model(Quotex)

    order_type = "BUY" if data["direction"].upper() == "CALL" else "SELL"

    open_time = parse_time_aware(info_buy.get("openTime"))  # Ex.: parse_time é uma função util
    close_time = parse_time_aware(info_buy.get("closeTime"))

    trade_order = TradeOrder.objects.create(
        content_type=content_type,
        object_id=broker_obj.id,
        broker=broker_obj,
        order_type=order_type,
        amount=data["amount"],
        status="EXECUTED" if status_buy else "FAILED",
        id_trade=info_buy.get("id"),
        uid=info_buy.get("uid"),
        percent_profit=info_buy.get("percentProfit"),
        open_time=open_time,
        close_time=close_time,
        request_id=info_buy.get("requestId"),
        result=info_buy.get("profit", 0),
        request_body=info_buy,
    )
    return trade_order

