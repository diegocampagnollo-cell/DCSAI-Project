import asyncio
import json
import logging

logger = logging.getLogger("rpc_core")
logging.basicConfig(level=logging.INFO, format='%(message)s')


# ==========================================================
#  RPC Connection helper
# ==========================================================
class RPCConnection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.addr = writer.get_extra_info("peername")

    async def recv(self):
        try:
            data = await self.reader.readline()
            if not data:
                return None
            return json.loads(data.decode("utf-8").strip())
        except Exception:
            return None

    async def send(self, msg):
        try:
            payload = (json.dumps(msg) + "\n").encode("utf-8")
            self.writer.write(payload)
            await self.writer.drain()
        except Exception:
            pass

    def close(self):
        try:
            self.writer.close()
        except Exception:
            pass


# ==========================================================
#  RPC Server com autenticação básica
# ==========================================================
class RPCServer:
    """
    Servidor RPC com handshake simples (token compartilhado).
    """
    def __init__(self, host="0.0.0.0", port=22888, auth_token="DCS_AUTH_1"):
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self._server = None
        self._conns = set()
        self._lock = asyncio.Lock()

    async def _handle_client(self, reader, writer):
        conn = RPCConnection(reader, writer)
        async with self._lock:
            self._conns.add(conn)

        try:
            # --- 1️⃣ Espera handshake inicial ---
            msg = await conn.recv()
            if not msg or msg.get("method") != "hello":
                logger.warning(f"[CORE][RX] invalid hello from {conn.addr}")
                await conn.send({"type": "error", "error": "missing_hello"})
                conn.close()
                return

            token = msg.get("params", {}).get("token")
            if token != self.auth_token:
                logger.warning(f"[CORE][RX] auth failed from {conn.addr}")
                await conn.send({"type": "error", "error": "auth_failed"})
                conn.close()
                return

            # --- 2️⃣ Handshake aceito ---
            await conn.send({"type": "response", "result": {"status": "ok"}})
            logger.info(f"[CORE][RX] auth ok ← {conn.addr}")

            # --- 3️⃣ Loop principal de mensagens ---
            while True:
                msg = await conn.recv()
                if msg is None:
                    break

                typ = msg.get("type", "").lower() if isinstance(msg, dict) else ""
                if typ in ("request", "req"):
                    method = msg.get("method")
                    if method == "ping":
                        await conn.send({
                            "type": "response",
                            "id": msg.get("id"),
                            "result": {"pong": True}
                        })
                    else:
                        await conn.send({
                            "type": "response",
                            "id": msg.get("id"),
                            "result": {"ok": True}
                        })
                elif typ in ("notify", "notification"):
                    logger.info(f"[CORE][RX] notify {msg.get('method')} ← {msg.get('params')}")
        except Exception as e:
            logger.warning(f"[CORE][RX] client error {e}")
        finally:
            conn.close()
            async with self._lock:
                if conn in self._conns:
                    self._conns.remove(conn)
            logger.info(f"[CORE][RX] disconnect ← {conn.addr}")

    async def start(self):
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f"[CORE][TX] listening → {self.host}:{self.port}")
        async with self._server:
            await self._server.serve_forever()
