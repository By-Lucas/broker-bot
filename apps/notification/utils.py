from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification_to_user(user_id, notification):
    """
    Envia uma notificação ao WebSocket do usuário específico.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_id}",
        {
            "type": "send_notification",
            "notification": {
                "title": notification.title,
                "description": notification.description,
                "html_content": notification.html_content,
                "url_redirect": notification.url_redirect,
                "type": notification.type,
            },
        }
    )
