import asyncio
import json
import logging

logger = logging.getLogger("rpc_panel")
logging.basicConfig(level=logging.INFO, format='%(message)s')


# ==========================================================
#  Painel RPC – cliente com handshake e token
# ==========================================================
AUTH_TOKEN = "DCS_AUTH_1"   # deve bater com o do core
CORE_HOST = "127.0.0.1"
CORE_PORT = 22888


async def run_panel():
    while True:
        try:
            print("[PANEL] Starting auto-discovery...")
            reader, writer = await asyncio.open_connection(CORE_HOST, CORE_PORT)
            print(f"[PANEL][TX] connected → {CORE_HOST}:{CORE_PORT}")

            # --- envia hello + token ---
            hello_msg = {
                "type": "request",
                "method": "hello",
                "params": {"token": AUTH_TOKEN}
            }
            writer.write((json.dumps(hello_msg) + "\n").encode())
            await writer.drain()

            # --- aguarda resposta ---
            data = await reader.readline()
            if not data:
                raise ConnectionError("no response")
            resp = json.loads(data.decode().strip())

            if resp.get("result", {}).get("status") == "ok":
                print("[PANEL] Auth OK ✅ – link established.")
            else:
                print("[PANEL] Auth failed ❌ – closing.")
                writer.close()
                await writer.wait_closed()
                await asyncio.sleep(3)
                continue

            # --- agora envia um ping periódico ---
            while True:
                ping_msg = {"type": "request", "method": "ping", "id": 1}
                writer.write((json.dumps(ping_msg) + "\n").encode())
                await writer.drain()
                data = await reader.readline()
                if not data:
                    raise ConnectionError("core disconnected")
                resp = json.loads(data.decode().strip())
                print("[PANEL][RX]", resp)
                await asyncio.sleep(5)

        except Exception as e:
            print(f"[PANEL][ERR] connection lost: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_panel())
