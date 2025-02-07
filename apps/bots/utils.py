import asyncio
import datetime
from decimal import Decimal

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .constants import PARITIES
from trading.models import TradeOrder
from integrations.models import Quotex, QuotexManagement


def parse_time_aware(timestr):
    naive_dt = datetime.datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    # Converte o datetime ingênuo no timezone definido no settings.py
    aware_dt = timezone.make_aware(naive_dt, timezone.get_default_timezone())
    return aware_dt


async def wait_until_second(second=59):
    """
    Aguarda até que datetime.now().second == second.
    Cuidado com latências de rede ou possíveis atrasos de execução.
    """
    while True:
        now = datetime.datetime.now()
        if now.second == second:
            # Opcional: ajustar para quebrar no milissegundo 0, se quiser mais precisão
            break
        # Dorme apenas frações de segundo para não perder o timing
        await asyncio.sleep(0.01)


def is_valid_trader(qx: Quotex, qx_manager:QuotexManagement):
    """
    Verifica se um trader está apto a operar na Quotex.
    Retorna True se estiver elegível, False caso contrário.
    """

    # 1. O cliente precisa estar ativo e o robô ligado
    if not qx.is_active or not qx.is_bot_active:
        return False

    # 2. Se está no período de teste, validar a data de expiração
    if qx.test_period and qx.test_expiration:
        if qx.test_expiration < datetime.datetime.now():
            return False  # Teste expirado

    # 3. Obtém a moeda e saldo do cliente
    currency = qx.currency_symbol  # Ex: "R$" ou "US$"
    balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance

    # 4. Define os valores mínimos exigidos
    min_balance = Decimal("5") if currency == "R$" else Decimal("1")
    min_entry_value = min_balance

    # 5. Verifica se o saldo da conta é suficiente para operar
    if balance < min_balance:
        return False

    # 6. Obtém o gerenciamento do cliente para validar a entrada
    management = qx_manager
    if management:
        entry_value = management.entry_value

        # 7. Verifica se o valor de entrada é maior que o saldo disponível
        if entry_value > balance:
            return False

    return True  # Tudo certo para operar!



def calculate_entry_amount(qx, qx_manager):
    """
    Calcula o valor da entrada considerando:
    - Percentual da banca (Stopwin / Stoploss)
    - Recuperação automática após 3 Loss seguidos
    - Valor mínimo de entrada (R$5 ou $1)
    """

    # 📌 Define a moeda e valor mínimo de entrada
    min_entry_value = Decimal("5") if qx.currency_symbol == "R$" else Decimal("1")

    # 📌 Obtém saldo da banca conforme o tipo de conta
    balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance

    # 📌 Obtém o gerenciamento ativo
    stop_loss = qx_manager.stop_loss
    stop_win = qx_manager.stop_gain
    entry_percent = qx_manager.entry_value  # Percentual de entrada

    # 📌 Calcula entrada baseada no percentual da banca
    base_entry = (balance * entry_percent) / 100

    # 📌 Verifica histórico de Loss seguidos
    recent_trades = TradeOrder.objects.filter(broker=qx).order_by("-created_at")[:3]
    loss_count = sum(1 for trade in recent_trades if trade.order_result_status == "LOSS")

    if loss_count == 3:
        # 📌 Aplicar recuperação se houver 3 Loss seguidos
        total_loss = sum(trade.result for trade in recent_trades if trade.result < 0)
        recovery_amount = abs(total_loss) + stop_win
        entry_value = min(recovery_amount, balance)  # Não ultrapassa o saldo
        print(f"🚨 {qx.email} está em recuperação! Nova entrada: {entry_value}")
    else:
        entry_value = base_entry

    # 📌 Garante que a entrada seja no mínimo R$5 ou $1
    return max(entry_value, min_entry_value)


def normalize_parities(raw_parities, payout_min=80):
    """
    Normaliza os pares de moedas removendo "(OTC)" e adicionando "_otc" no final se necessário.
    Filtra os pares com payouts maiores ou iguais ao valor definido.
    
    :param raw_parities: Dicionário retornado pela API contendo os pares e payouts.
    :param payout_min: Percentual mínimo de payout (default é 80%).
    :return: Dicionário de pares normalizados e seus respectivos payouts.
    """

    normalized_parities = {}

    for pair, info in raw_parities.items():
        payout = info.get("payment", 0)

        # Verifica se o payout é maior ou igual ao mínimo
        if payout >= payout_min:
            normalized_pair = pair.replace(" (OTC)", "_otc").replace("/", "")  # Converte "USDJPY (OTC)" para "USDJPY_otc"
            
            # Mantém apenas os pares que estão na lista definida
            if normalized_pair.replace("_otc", "") in PARITIES:
                normalized_parities[normalized_pair] = payout

    return normalized_parities


def check_loss_streak(qx):
    """
    Verifica quantas perdas consecutivas o trader teve.
    """
    from trading.models import TradeOrder

    last_trades = TradeOrder.objects.filter(content_type=ContentType.objects.get_for_model(Quotex), object_id=qx.id, order_result_status="LOSS").order_by("-created_at")[:3]

    return len(last_trades) if len(last_trades) == 3 else 0


def get_accumulated_loss(qx):
    """
    Calcula o prejuízo acumulado nos últimos trades perdidos.
    """
    from trading.models import TradeOrder

    loss_trades = TradeOrder.objects.filter(content_type=ContentType.objects.get_for_model(Quotex), object_id=qx.id, order_result_status="LOSS").order_by("-created_at")[:3]

    return sum(abs(trade.result) for trade in loss_trades if trade.result)
