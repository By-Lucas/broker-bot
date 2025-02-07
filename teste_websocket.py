import asyncio
import websockets
import json
from datetime import datetime

async def send_trade_simulation():
    uri = "ws://localhost:8000/ws/trader/quotex/"  # Atualize a URL conforme necessário

    async with websockets.connect(uri) as websocket:
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"📡 Nova atualização recebida:\n{json.dumps(data, indent=4)}")
            except websockets.ConnectionClosed as e:
                print(f"❌ Conexão WebSocket encerrada: {e}")
                break
            except Exception as e:
                print(f"⚠ Erro ao receber dados: {e}")

# Rodar o script continuamente
if __name__ == "__main__":
    asyncio.run(send_trade_simulation())
