import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from integrations.models import Quotex
from trading.models import TradeOrder


class TradesConsumer(AsyncWebsocketConsumer):
    """ WebSocket Consumer para receber e enviar atualizações de trades """

    async def connect(self):
        """ Estabelece a conexão WebSocket """
        self.broker_name = self.scope['url_route']['kwargs']['broker_name']
        self.user = self.scope['user']
        self.room_group_name = f'bot_trades_{self.broker_name}'

        # ✅ Adiciona o usuário ao grupo WebSocket específico da corretora
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send_websocket_user(event={"action":"start"})

        print(f"🚀 WebSocket conectado: {self.user} na corretora {self.broker_name}")

    async def disconnect(self, close_code):
        """ Remove o usuário do grupo WebSocket ao desconectar """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"❌ WebSocket desconectado: {self.user} na corretora {self.broker_name}")

    async def receive(self, text_data):
        """ Processa mensagens recebidas do WebSocket e envia para o grupo """
        data = json.loads(text_data)
        print(f"📩 Dados recebidos no WebSocket: {data}")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_websocket_user',
                'data': data
            }
        )

    async def send_websocket_user(self, event):
        action = event.get("action", "")
        data = event.get("data", {})

        if action == "activate_bot":
            print(f"🔔 Robô ativado para: {data.get('email')}")

        # Envia uma resposta genérica para o cliente
        await self.send(json.dumps({
            "status": "Robô ativado via WebSocket",
            "action": action,
            "data": await self.get_trades_data(),
        }))


    async def get_trades_data(self):
        """ Obtém os dados de traders do usuário e retorna JSON formatado """

        # ✅ Buscar a conta Quotex do usuário de forma assíncrona
        user_account = await sync_to_async(lambda: Quotex.objects.filter(customer_id=self.user.id, is_active=True).first())()

        if not user_account:
            return {"error": "Conta não encontrada para esta corretora."}

        # ✅ Filtrar apenas os trades do usuário e da corretora
        trades_list = await sync_to_async(lambda: list(
            TradeOrder.objects.filter(broker=user_account, is_active=True).select_related("broker")
        ))()

        # ✅ Contagem total de trades e soma dos resultados
        total_trades = len(trades_list)
        total_results = float(sum(trade.result for trade in trades_list))

        # ✅ Contagem de status (WIN, LOSS, etc.)
        status_counts = {}
        for trade in trades_list:
            status_counts[trade.order_result_status] = status_counts.get(trade.order_result_status, 0) + 1

        # ✅ Lista de detalhes dos traders (convertendo Decimals para float)
        trade_details = [
            {
                "id_trade": trade.id_trade,
                "asset_order": trade.asset_order,
                "order_result_status": trade.order_result_status,
                "amount": float(trade.amount),
                "percent_profit": float(trade.percent_profit),
                "result": float(trade.result),
                "broker_email": trade.broker.email if trade.broker else "N/A",
            }
            for trade in trades_list
        ]

        # 🔥 PEGAR DADOS DA CONTA DO USUÁRIO (SALDO)
        account_balance = {
            "type": "REAL" if user_account.account_type == "REAL" else "DEMO",
            "balance": float(user_account.real_balance if user_account.account_type == "REAL" else user_account.demo_balance),
            "currency": user_account.currency_symbol or "R$"
        }

        # ✅ Retornar os dados formatados
        return {
            "total_trades": total_trades,
            "total_results": total_results,
            "status_counts": status_counts,
            "trade_details": trade_details,
            "account_balance": account_balance
        }
