# bots/tasks.py
import asyncio
import random
from celery import shared_task
from django.utils import timezone

from trading.models import TradeOrder
from bots.constants import PARITIES
from bots.quotex_management import QuotexManagement
from integrations.models import Quotex


@shared_task
def verify_and_update_quotex(quotex_id):
    """
    Verifica se as credenciais existem/funcionam, atualiza dados de perfil e saldo,
    e checa condições de saldo mínimo.
    """
    try:
        quotex = Quotex.objects.get(id=quotex_id)
    except Quotex.DoesNotExist:
        return {"error": f"Quotex ID {quotex_id} não encontrado."}

    # Inicializa o bot manager com as credenciais do cliente
    manager = QuotexManagement(
        email=quotex.email,
        password=quotex.password,
        account_type=quotex.account_type
    )

    # Tenta se conectar e obter dados
    connected = asyncio.run(manager.send_connect())
    if not connected:
        return {"error": f"Não foi possível conectar com Quotex para o usuário {quotex.email}."}

    profile_data = asyncio.run(manager.get_profile())
    balance_data = asyncio.run(manager.get_balance())

    if not profile_data:
        return {"error": f"Não foi possível obter dados de perfil para {quotex.email}."}

    try:
        # Conversão de string para decimal
        demo_balance = float(profile_data["demo_balance"])
        live_balance = float(profile_data["live_balance"])
        currency_symbol = profile_data["currency_symbol"]
        country_name = profile_data["country_name"]
        profile_id = profile_data["profile_id"]
        avatar = profile_data["avatar"]


        quotex.trader_id = profile_id
        quotex.demo_balance = demo_balance
        quotex.real_balance = live_balance
        quotex.currency_symbol = currency_symbol

        # Validação de saldo mínimo
        if quotex.account_type == "REAL":
            # Supondo que seja >= 5 (BRL)
            if live_balance < 5:
                # Faça algo (ex.: desabilitar a corretora para o cliente)
                quotex.is_active = False
        else:
            # Conta Prática
            if demo_balance < 1:
                # Saldo demo muito baixo para operar? 
                pass  # Defina a regra de negócio

        quotex.updated_at = timezone.now()
        quotex.save()

        # Se quiser atualizar também o Customer:
        customer = quotex.customer
        customer.country = country_name
        customer.trader_id = profile_id
        customer.avatar = avatar

        # Você poderia armazenar o profile_data inteiro em data_callback, se quiser.
        customer.data_callback = profile_data
        customer.save()

        return {
            "status": "success",
            "profile": profile_data,
            "balance": balance_data
        }
    except KeyError as e:
        return {"error": f"Chave não encontrada no retorno da API: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao atualizar dados: {str(e)}"}


@shared_task
def schedule_random_trades():
    """
    Tarefa que roda a cada 5 minutos (configurar no Celery Beat).
    Seleciona 20 usuários (ou corretores) por vez e executa
    ordens de buy/sell aleatórias.
    """
    # 1. Buscar contas ativas
    quotex_accounts = Quotex.objects.filter(is_active=True)

    # 2. Dividir em lotes (chunks) de 20
    chunk_size = 20
    total = quotex_accounts.count()
    for start in range(0, total, chunk_size):
        batch = quotex_accounts[start : start + chunk_size]
        for qx in batch:
            manager = QuotexManagement(
                email=qx.email,
                password=qx.password,
                account_type=qx.account_type
            )

            # 3. Escolher dados aleatórios
            asset = random.choice(PARITIES)
            direction = random.choice(["call", "put"])  # ou "BUY"/"SELL" dependendo da API
            duration = 60  # Exemplo: de 1 a 5 minutos
            amount = 5 # valor fixo ou também pode ser aleatório

            data = {
                "amount": amount,
                "asset": asset,
                "duration": duration,
                "direction": direction,
                "email": qx.email,
                "costumer_id": qx.customer.id,
                "broker_id": qx.id,
            }

            # 4. Chamar o método buy_sell
            status_buy, info_buy = asyncio.run(manager.buy_sell(data))
            #print(f"[{qx.email}] -> status: {status_buy}, info: {info_buy}")

    return "Tarefa concluída com sucesso!"


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

    manager = QuotexManagement(email, password, account_type)

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