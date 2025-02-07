# bots/tasks.py
import asyncio
from decimal import Decimal
import random
from celery import shared_task
from django.utils import timezone

from bots.services import send_trade_update
from bots.utils import calculate_entry_amount, is_valid_trader
from trading.models import TradeOrder
from bots.constants import PARITIES
from bots.quotex_management import QuotexManagement as BaseQuotex
from integrations.models import Quotex, QuotexManagement


@shared_task
def verify_and_update_quotex_task(quotex_id=None):
    """
    Verifica credenciais, atualiza perfil e saldo para um único Quotex ou para todos os ativos.
    Se `quotex_id` for None, atualiza todos os clientes ativos em lotes de 20.
    """
    # 1️⃣ Seleciona as contas a serem atualizadas
    if quotex_id:
        quotex_accounts = Quotex.objects.filter(id=quotex_id, is_active=True)
    else:
        quotex_accounts = Quotex.objects.filter(is_active=True)

    total_accounts = quotex_accounts.count()
    chunk_size = 20  # Processar 20 clientes por vez

    for start in range(0, total_accounts, chunk_size):
        batch = quotex_accounts[start : start + chunk_size]

        for quotex in batch:
            try:
                # ✅ Inicializa o gerenciador da Quotex
                manager = BaseQuotex(
                    email=quotex.email,
                    password=quotex.password,
                    account_type=quotex.account_type
                )


                # ✅ Obtém perfil e saldo
                profile_data = asyncio.run(manager.get_profile())
                if not profile_data :
                    print(f"Erro ao obter dados de {quotex.email}")
                    continue

                # ✅ Conversão de valores
                demo_balance = Decimal(str(profile_data["demo_balance"]))
                real_balance = Decimal(str(profile_data["live_balance"]))
                currency_symbol = profile_data.get("currency_symbol", "R$")
                country_name = profile_data.get("country_name", "")
                profile_id = profile_data.get("profile_id", "")
                avatar = profile_data.get("avatar", "")

                # ✅ Atualiza o Quotex no banco de dados
                quotex.trader_id = profile_id
                quotex.demo_balance = demo_balance
                quotex.real_balance = real_balance
                quotex.currency_symbol = currency_symbol

                # ✅ Valida saldo mínimo para operar
                if quotex.account_type == "REAL" and quotex.real_balance < 1:
                    quotex.is_bot_active = False  # Desativa se saldo for insuficiente
                elif quotex.account_type == "PRACTICE" and quotex.demo_balance < 1:
                    quotex.is_bot_active = False  # Desativa conta prática sem saldo

                quotex.updated_at = timezone.now()
                quotex.save()

                # ✅ Atualiza os dados do cliente associado
                customer = quotex.customer
                customer.country = country_name
                customer.trader_id = profile_id
                customer.avatar = avatar
                customer.data_callback = profile_data  # Armazena dados do perfil
                customer.save()

                print(f"✅ Quotex atualizado: {quotex.email}")

            except KeyError as e:
                print(f"🚨 Erro de chave ausente: {str(e)}")
            except Exception as e:
                print(f"🚨 Erro ao processar {quotex.email}: {str(e)}")

    return {"status": "success", "updated_accounts": total_accounts}


@shared_task
def execute_random_trade(quotex_id, data):
    """
    Executa uma entrada (trade) para uma única conta Quotex,
    considerando o gerenciamento de risco.
    """

    # Obter a instância do Quotex
    qx = Quotex.objects.get(id=quotex_id)

    # Criar o gerenciador
    manager = BaseQuotex(
        email=qx.email,
        password=qx.password,
        account_type=qx.account_type
    )

    # Executar a operação
    status_buy, info_buy = asyncio.run(manager.buy_sell(data))


    return {
        "email": qx.email,
        "status_buy": status_buy,
        "info_buy": info_buy
    }


@shared_task
def schedule_random_trades():
    """
    A cada 20 minutos, agenda trades aleatórios para clientes ativos na Quotex.
    Processa em lotes de 20 para evitar sobrecarga.
    """

    chunk_size = 20  # Processamos 20 contas por vez
    quotex_accounts = Quotex.objects.filter(is_active=True, is_bot_active=True)
    total = quotex_accounts.count()

    for start in range(0, total, chunk_size):
        batch = quotex_accounts[start : start + chunk_size]

        for qx in batch:
            # ✅ Verifica se o cliente pode operar
            qx_manager = QuotexManagement.objects.filter(customer=qx.customer).first()

            if not is_valid_trader(qx, qx_manager):
                continue  # Ignora clientes que não passaram na validação

            # 🎯 Obter a entrada considerando gerenciamento
            amount = float(qx_manager.entry_value) or float(5)

            # Escolher um ativo aleatório
            asset = random.choice(PARITIES)

            # Escolher se será compra ou venda
            direction = random.choice(["call", "put"])

            # Definir tempo da ordem (exemplo: 60 segundos)
            duration = 60

            # Montar os parâmetros da ordem
            data = {
                "amount": amount,
                "asset": asset,
                "duration": duration,
                "direction": direction,
                "email": qx.email,
                "costumer_id": qx.customer.id,
                "broker_id": qx.id,

            }

            result = execute_random_trade.delay(qx.id, data)

    return f"{total} trades agendados com sucesso!"

@shared_task
def check_trade_status_task(trade_order_id):
    """
    Verifica e atualiza o status de um TradeOrder,
    usando a API da Quotex.
    """
    try:
        # Carrega a ordem
        trade_order = TradeOrder.objects.get(id=trade_order_id)
    except TradeOrder.DoesNotExist:
        return {"error": f"TradeOrder {trade_order_id} não encontrado."}

    # Obtém o ID da trade na corretora (id_trade)
    trader_id = trade_order.id_trade
    if not trader_id:
        return {"error": "Essa TradeOrder não possui id_trade para verificar."}
    
    trader_id = trade_order.id_trade
    if trade_order.order_result_status in ["WIN", "LOSS", "DOGI"]:
        return {"error": "Essa TradeOrder já foi verificado."}

    # Precisamos do email, password e account_type para conectar
    # Ao broker (Quotex). Se você tiver armazenado isso:
    broker_obj = trade_order.broker  # se 'broker' for a GenericForeignKey para o modelo Quotex
    email = broker_obj.email
    password = broker_obj.password
    account_type = broker_obj.account_type

    manager = BaseQuotex(email, password, account_type)

    # Faz a verificação de forma assíncrona:
    status = asyncio.run(manager.verify_trader(trader_id))

    # Decida como mapear esse `status` para o modelo
    # Ex.: se status["status"] == "WIN", trade_order.order_result_status = "WIN"
    if "status" in status:
        if status["status"] == True:
            trade_order.order_result_status = "WIN"
            trade_order.result = trade_order.result
        elif status["status"] == False:
            trade_order.order_result_status = "LOSS"
            trade_order.result = f"-{trade_order.amount}"
        else:
            trade_order.order_result_status = "DOGI"
            trade_order.result = 0

    # Se houver um lucro adicional
    if "profit" in status:
        trade_order.result = status["profit"]

    # Marca como executada
    trade_order.status = "EXECUTED"
    trade_order.save()

    return {"success": True, "new_status": trade_order.order_result_status}