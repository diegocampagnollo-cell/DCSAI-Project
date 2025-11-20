import asyncio
import logging

HOST = "127.0.0.1"
PORT = 22000

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Conectando ao core {HOST}:{PORT}")
    reader, writer = await asyncio.open_connection(HOST, PORT)
    msg = await reader.readline()
    logging.info(f"Recebido do core: {msg.decode().strip()}")
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())