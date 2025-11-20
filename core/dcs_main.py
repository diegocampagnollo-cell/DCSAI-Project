import psutil
import json
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

HOST = "localhost"
PORT = 8765

async def handle_client(ws):
    print("[CORE] Cliente conectado!")

    try:
        while True:

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent

            msg = {
                "type": "stats",
                "cpu": cpu,
                "ram": ram,
                "message": "Core ativo (heartbeat)"
            }

            await ws.send(json.dumps(msg))

            await asyncio.sleep(1)

    except ConnectionClosedOK:
        print("[CORE] Cliente saiu normalmente.")

    except ConnectionClosedError as e:
        print("[CORE] Conexão fechada inesperadamente:", e)

    except Exception as e:
        print("[CORE] Erro interno:", e)

    finally:
        print("[CORE] Cliente desconectado.")

async def main():
    print(f"🔥 Core WebSocket ativo em ws://{HOST}:{PORT}")

    async with websockets.serve(
        handle_client,
        HOST,
        PORT,
        ping_interval=None,
        ping_timeout=None,
    ):
        await asyncio.Future()  # mantém vivo

if __name__ == "__main__":
    asyncio.run(main())
