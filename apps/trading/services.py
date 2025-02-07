import json
from django.db.models import Sum, Count
from asgiref.sync import sync_to_async
from trading.models import TradeOrder
from integrations.models import Quotex



async def get_detailed_dashboard_data(trades_list, user):
    """ Retorna os dados detalhados apenas para os traders do usuário """

    # ✅ Converte para queryset de forma assíncrona
    total_trades = len(trades_list)
    total_results = sum(trade.result for trade in trades_list)

    # Contagem de status
    status_counts = {}
    for trade in trades_list:
        status_counts[trade.order_result_status] = status_counts.get(trade.order_result_status, 0) + 1

    # Detalhes dos traders
    trade_details = [
        {
            "id_trade": trade.id_trade,
            "asset_order": trade.asset_order,
            "order_result_status": trade.order_result_status,
            "amount": float(trade.amount),
            "percent_profit": float(trade.percent_profit),
            "result": float(trade.result),
            "broker_email": trade.broker.email,  # Incluindo nome do trader (corretora)
        }
        for trade in trades_list
    ]

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
