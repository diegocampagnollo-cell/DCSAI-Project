import asyncio
import logging

logging.basicConfig(level=logging.INFO)
HOST = "0.0.0.0"
PORT = 22000

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    logging.info(f"Cliente conectado: {addr}")
    writer.write(b"hello from core\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def main():
    logging.info("Iniciando servidor RPC de teste...")
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f"Servidor escutando em {addrs}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
