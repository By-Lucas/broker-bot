import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from integrations.models import Quotex
from trading.models import TradeOrder
from trading.services import get_detailed_dashboard_data


class TradesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.broker_name = self.scope['url_route']['kwargs']['broker_name']  # 🆕 Captura o broker_name da URL
        self.user = self.scope['user']
        self.room_group_name = f'bot_trades_{self.broker_name}'  # 🔥 Cria um grupo único por corretora e usuário

        # ✅ Adiciona o usuário ao grupo WebSocket específico da corretora
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"🚀 Conexão WebSocket estabelecida para {self.user} na corretora {self.broker_name}")

        # ✅ Envia os dados iniciais para o usuário autenticado
        await self.send_trades_update()

    async def disconnect(self, close_code):
        # ❌ Remove o usuário do grupo WebSocket ao desconectar
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"❌ WebSocket desconectado para {self.user.email} na corretora {self.broker_name}")

    async def receive(self, text_data):
        """ Escuta mensagens recebidas do WebSocket (caso precise de comandos do front-end) """
        data = json.loads(text_data)
        action = data.get("action", "")

        if action == "update":
            await self.send_trades_update()
    
    async def bot_control(self, event):
        data = json.loads(event)
        action = data.get("action", "")

        await self.send_trades_update()

    async def send_trades_update(self):
        """ Envia os dados de traders do usuário para o cliente WebSocket """
        try:
            # ✅ Filtra a conta Quotex do usuário e da corretora
            user_account = await sync_to_async(Quotex.objects.filter(customer=self.user).first)()
            
            if not user_account:
                await self.send(json.dumps({"error": "Conta não encontrada para esta corretora."}))
                return

            # ✅ Filtra apenas os trades do usuário e da corretora correta
            trades_user = TradeOrder.objects.filter(broker=user_account)

            # ✅ Obtém os dados detalhados (cotação e saldo incluídos)
            trades_data = await get_detailed_dashboard_data(trades_user, self.user)

            # ✅ Formatar e enviar os dados via WebSocket
            json_data = json.dumps(trades_data)
            await self.send(json_data)

        except Exception as e:
            print(f"⚠ Erro ao enviar dados via WebSocket: {e}")
            await self.send(json.dumps({"error": "Erro ao buscar dados dos traders."}))
