import asyncio
import websockets

async def main():
    while True:
        try:
            print("Conectando...")
            ws = await websockets.connect("ws://localhost:8765")
            print("Conectado! Aguardando mensagens...")

            async for msg in ws:
                print("Mensagem recebida:", msg)

        except Exception as e:
            print("ERRO:", e)
            await asyncio.sleep(2)

asyncio.run(main())
