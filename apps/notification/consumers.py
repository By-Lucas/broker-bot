import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from notification.models import BaseNotification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ Conecta o WebSocket e envia a última notificação ativa ao usuário autenticado. """
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{user.id}"

        # Adiciona o usuário ao grupo WebSocket
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Envia a última notificação ativa ao conectar
        await self.send_last_active_notification(user)

    async def disconnect(self, close_code):
        """ Remove o usuário do grupo WebSocket ao desconectar. """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """ Processa mensagens recebidas do WebSocket (caso necessário no futuro). """
        data = json.loads(text_data)
        print(f"📩 Dados recebidos no WebSocket: {data}")

    async def send_notification(self, event):
        """ Envia uma nova notificação para o WebSocket do usuário. """
        notification_data = event.get("notification", {})
        if notification_data:
            await self.send(json.dumps(notification_data))

    async def send_last_active_notification(self, user):
        """ Busca e envia a última notificação ativa do usuário. """
        notification = await sync_to_async(
            lambda: BaseNotification.objects.filter(
                user=user, is_active=True
            ).order_by('-created_date').first()
        )()

        if notification:
            notification_data = {
                "type": notification.type,
                "title": notification.title,
                "description": notification.description,
                "value": float(notification.value) if notification.value else None,
                "created_date": notification.created_date.strftime("%d/%m/%Y %H:%M"),
                "modified_date": notification.modified_date.strftime("%d/%m/%Y %H:%M"),
                "url_redirect": notification.url_redirect,
                "html_content": notification.html_content or None
            }
            await self.send(json.dumps(notification_data))
        else:
            await self.send(json.dumps({"message": "Nenhuma notificação ativa."}))
