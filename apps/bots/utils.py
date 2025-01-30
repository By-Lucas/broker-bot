import asyncio
import datetime
from decimal import Decimal

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

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
    Calcula o valor da entrada com base no gerenciamento escolhido.
    Se houver 3 Loss seguidos, ativa a entrada de recuperação.
    """

    # Obtém o saldo da conta do cliente
    available_balance = qx.real_balance if qx.account_type == "REAL" else qx.demo_balance

    # Define a entrada normal
    base_entry = Decimal(qx_manager.entry_value)

    # Verifica histórico de perdas consecutivas
    loss_streak = check_loss_streak(qx)

    if loss_streak >= 3:
        # Calcula o prejuízo acumulado e a entrada de recuperação
        accumulated_loss = get_accumulated_loss(qx)
        stop_win = qx_manager.stop_gain

        recovery_amount = accumulated_loss + stop_win

        # Se o valor for maior que a banca, usa o saldo total disponível
        entry_amount = min(recovery_amount, available_balance)
        print(f"⚠️ Ativando recuperação para {qx.email}. Nova entrada: {entry_amount}")
    else:
        entry_amount = base_entry

    # Garante que a entrada não seja menor que o mínimo permitido
    min_entry = Decimal("5") if qx.currency_symbol == "R$" else Decimal("1")
    return max(entry_amount, min_entry)


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
