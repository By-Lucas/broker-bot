import json
from decimal import Decimal
from django.utils.timezone import now
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from trading.models import TradeOrder
from integrations.models import Quotex, QuotexManagement
from notification.models import BaseNotification


@receiver(post_save, sender=TradeOrder)
def check_stop_gain(sender, instance, **kwargs):
    """ 🚨 Verifica Stop Gain e período de teste ao atualizar um trade. """
    
    # Somente executa quando um trade finalizado for atualizado
    if instance.order_result_status not in ["WIN", "LOSS"]:
        return

    broker = instance.broker
    customer = broker.customer

    # Obtém a configuração de gerenciamento do cliente
    try:
        management = QuotexManagement.objects.get(customer=customer)
    except QuotexManagement.DoesNotExist:
        return  # Ignora se não houver configuração

    # Calcula o resultado total do cliente considerando apenas traders finalizados
    total_result = TradeOrder.objects.filter(
        is_active=True,
        broker=broker,
        order_result_status__in=["WIN", "LOSS"]
    ).aggregate(total=Sum("result"))["total"] or Decimal("0.00")

    print(f"🔍 Total atual: {total_result} | Stop Gain: {management.stop_gain}")

    # 🚨 Verifica se atingiu o **Stop Gain**
    if total_result >= management.stop_gain:
        broker.is_bot_active = False  # Desativa o robô
        broker.save()

        # Cria uma notificação de Stop Gain
        notification = BaseNotification.objects.create(
            user=customer,
            type="stop_gain",
            title="🚀 Stop Gain atingido!",
            description=f"Seu lucro de {total_result} atingiu o limite definido ({management.stop_gain}).",
            value=total_result,
            is_active=True,
        )

        print(f"✅ [STOP WIN] Notificação enviada para {customer.email}")

        # Envia a notificação via WebSocket
        send_notification_via_websocket(customer.id, notification.to_dict())

    # 🚨 **Verifica se o período de teste expirou**
    if broker.test_period and broker.test_expiration and now() >= broker.test_expiration:
        broker.is_active = False  # Desativa a conta do usuário no período de teste
        broker.is_bot_active = False  # Desativa o robô também
        broker.save()

        notification = BaseNotification.objects.create(
            user=customer,
            type="access_interrupted",
            title="⏳ Período de teste encerrado!",
            description="Seu período de teste foi encerrado automaticamente.",
            is_active=True,
        )

        print(f"⏳ [TESTE EXPIRADO] Robô desativado para {customer.email}")

        send_notification_via_websocket(customer.id, notification.to_dict())

    # 🚨 **Se o usuário está no período de teste e atingiu a meta do Stop Win**
    elif broker.test_period and total_result >= management.stop_gain:
        notification = BaseNotification.objects.create(
            user=customer,
            type="maximum_profit",
            title="🎯 Meta atingida no período de teste!",
            description=f"Parabéns! Você atingiu {total_result} durante seu período de teste.",
            is_active=True,
        )

        print(f"🔔 [PERÍODO DE TESTE] Usuário {customer.email} bateu a meta de Stop Win.")

        send_notification_via_websocket(customer.id, notification.to_dict())

    # 🚨 Stop Loss REMOVIDO (Comentado)
    # elif total_result <= -management.stop_loss:
    #     broker.is_bot_active = False  # Desativa o robô
    #     broker.save()
    #
    #     notification = BaseNotification.objects.create(
    #         user=customer,
    #         type="stop_loss",
    #         title="🔻 Stop Loss atingido!",
    #         description=f"Sua perda de {total_result} atingiu o limite definido ({management.stop_loss}).",
    #         value=total_result,
    #         is_active=True,
    #     )
    #
    #     send_notification_via_websocket(customer.id, notification.to_dict())

def send_notification_via_websocket(user_id, notification_data):
    """ Envia a notificação via WebSocket para o usuário """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_id}",
        {"type": "send_notification", "notification": notification_data}
    )
