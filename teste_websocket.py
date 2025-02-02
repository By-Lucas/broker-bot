import asyncio
import websockets
import json


async def test_websocket():
    websocket_url = "ws://localhost:8000/ws/trader/quotex/"  # Altere para o URL correto do seu WebSocket
    kwargs={"broker":"quotex"}
    async with websockets.connect(websocket_url) as websocket:
        print("✅ Conectado ao WebSocket!")


        while True:
            try:
                # Aguarda mensagens do WebSocket
                message = await websocket.recv()
                data = json.loads(message)
                print("📡 Mensagem recebida:")
                print(json.dumps(data, indent=4))
            except websockets.ConnectionClosed as e:
                print(f"❌ Conexão encerrada: {e}")
                break
            except Exception as e:
                print(f"⚠ Erro: {e}")

# Inicia o loop de eventos
asyncio.run(test_websocket())