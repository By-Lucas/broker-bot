import requests

from core.models import Notification
from permissions.models import BrokerPermission


async def filed_login(email: str, message: str) -> dict:
    permission = BrokerPermission.objects.filter(email=email).first()
    user = None
    if permission:
        message = f"Email ou senha incorreta para Quotex: {email}"
        user = permission.user if permission.user is not None else None

    # Cria a notificação
    notification = Notification.objects.create(
        title="FALHA NO LOGIN",
        message=message,
        icon="fa fa-info-circle",
        is_active=True,
        user=user,
    )
    return notification
