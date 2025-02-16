from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification_to_user(user_id):
    """
    Envia uma notificação ao WebSocket do usuário específico.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_id}",
        {
            "type": "send_notification",
            "notification": {
                "user_id":user_id,
                "type":"clean_notification"
            },
        }
    )
