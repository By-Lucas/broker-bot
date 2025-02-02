import json
from django.db.models import Sum, Count
from asgiref.sync import sync_to_async
from trading.models import TradeOrder
from integrations.models import Quotex


async def get_detailed_dashboard_data(trades_queryset, user):
    """ Retorna os dados detalhados apenas para os traders do usuário """

    # 🔥 Filtra os traders corretamente
    trades_queryset = await sync_to_async(lambda: TradeOrder.objects.filter(broker__customer=user))()

    total_trades = await sync_to_async(lambda: trades_queryset.count())()
    total_results = await sync_to_async(
        lambda: float(trades_queryset.aggregate(total=Sum("result"))["total"] or 0)
    )()

    # Contagem de status
    status_counts_raw = await sync_to_async(lambda: list(
        trades_queryset.values("order_result_status").annotate(count=Count("id"))
    ))()
    status_counts = {status["order_result_status"]: status["count"] for status in status_counts_raw}

    # Detalhes dos traders
    trade_details = await sync_to_async(lambda: list(
        trades_queryset.values(
            "id_trade",
            "asset_order",
            "order_result_status",
            "amount",
            "percent_profit",
            "result",
            "broker__email"  # Incluindo nome do trader (corretora)
        )
    ))()

    # **Formatação dos dados para evitar erro Decimal**
    for trade in trade_details:
        trade["result"] = float(trade["result"]) if trade["result"] else 0
        trade["amount"] = float(trade["amount"]) if trade["amount"] else 0
        trade["percent_profit"] = float(trade["percent_profit"]) if trade["percent_profit"] else 0

    # 🔥 PEGAR DADOS DA CONTA DO USUÁRIO
    account_balance = {
        "type": "DEMO",
        "balance": 0.0,
        "currency": "R$",
    }

    user_account = await sync_to_async(lambda: Quotex.objects.filter(customer=user).first())()
    if user_account:
        account_balance["type"] = "REAL" if user_account.account_type == "REAL" else "DEMO"
        account_balance["balance"] = float(user_account.real_balance if user_account.account_type == "REAL" else user_account.demo_balance)
        account_balance["currency"] = user_account.currency_symbol or "R$"

    return {
        "total_trades": total_trades,
        "total_results": total_results,
        "status_counts": status_counts,
        "trade_details": trade_details,
        "account_balance": account_balance,  # ✅ Adicionado o saldo do usuário
    }
