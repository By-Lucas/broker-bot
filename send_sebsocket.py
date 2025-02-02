import asyncio
import websockets
import json
from datetime import datetime
import random

async def send_trades():
    uri = "ws://localhost:8000/ws/trader/quotex/"  # Atualize a URL conforme necessário

    async with websockets.connect(uri) as websocket:
        while True:
            trade_data = {
                "par": random.choice(["EURUSD", "GBPJPY", "USDJPY", "AUDCAD"]),  # Moeda aleatória
                "direcion": random.choice(["call", "put"]),  # Direção aleatória
                "value": round(random.uniform(10, 1000), 2),  # Valor aleatório
                "result": round(random.uniform(-50, 200), 2),  # Lucro/prejuízo aleatório
                "status": random.choice(["win", "loss"]),  # WIN ou LOSS
                "execution_datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Data e hora
                "email": "lucasdev@gmail.com",
                "broker": "quotex",
            }

            # Enviar trade simulado para o WebSocket
            await websocket.send(json.dumps(trade_data))
            print(f"✅ Trade enviado: {trade_data}")

            # Tempo aleatório entre envios (simulando operações reais)
            await asyncio.sleep(random.uniform(5, 10))

# Rodar o script continuamente
if __name__ == "__main__":
    asyncio.run(send_trades())
