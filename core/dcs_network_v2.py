import socket
import threading
import json
import time
import logging

# ==========================================================
# DCs.AI – Network Manager (Patch 116.3.9.3)
# Bridge Interlink + Peer Cache + AutoSync
# ==========================================================
# Responsável por descoberta, cache e sincronização de peers
# ==========================================================

DISCOVERY_PORT = 56062
SYNC_PORT = 22000
BROADCAST_INTERVAL = 5.0
BUFFER_SIZE = 4096


class PeerCache:
    """Mantém registro dos peers descobertos para evitar repetição."""
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def add(self, addr):
        with self._lock:
            if addr not in self._cache:
                self._cache[addr] = time.time()
                return True
            return False

    def get_all(self):
        with self._lock:
            return list(self._cache.keys())


class DCSNetworkManager:
    def __init__(self, mode="auto"):
        self.mode = mode
        self.running = False
        self.peers = PeerCache()
        self.sock = None
        self.logger = logging.getLogger("network")

    # ----------------------------------------------------------
    # Inicializa o servidor de rede principal
    # ----------------------------------------------------------
    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("0.0.0.0", DISCOVERY_PORT))

        self.logger.info(f"[DCS114] Server listening on 0.0.0.0:{SYNC_PORT} (mode={self.mode})")

        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()

    # ----------------------------------------------------------
    # Loop de recepção — escuta mensagens de broadcast
    # ----------------------------------------------------------
    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                if addr[0].startswith("127."):  # ignora localhost
                    continue
                msg = json.loads(data.decode(errors="ignore"))

                if msg.get("type") == "hello":
                    if self.peers.add(addr):
                        print(f"[DISCOVERY] Found peer {addr}")
                elif msg.get("type") == "sync_request":
                    self._send_state(addr)

            except Exception as e:
                self.logger.warning(f"[NETWORK] listen error: {e}")

    # ----------------------------------------------------------
    # Envia broadcast periódico com presença local
    # ----------------------------------------------------------
    def _broadcast_loop(self):
        while self.running:
            try:
                hello = json.dumps({"type": "hello", "node": socket.gethostname()}).encode()
                self.sock.sendto(hello, ("255.255.255.255", DISCOVERY_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                self.logger.error(f"[NETWORK] broadcast error: {e}")

    # ----------------------------------------------------------
    # Envia estado local para peers sob demanda
    # ----------------------------------------------------------
    def _send_state(self, addr):
        try:
            msg = json.dumps({"type": "state", "uptime": time.time()})
            self.sock.sendto(msg.encode(), addr)
            print(f"[SYNC] Pushed state to {addr[0]}:{SYNC_PORT}")
        except Exception as e:
            self.logger.error(f"[NETWORK] state send error: {e}")

    # ----------------------------------------------------------
    # Solicita estado dos peers conhecidos
    # ----------------------------------------------------------
    def request_state_all(self):
        for peer in self.peers.get_all():
            try:
                msg = json.dumps({"type": "sync_request"})
                self.sock.sendto(msg.encode(), peer)
            except Exception as e:
                self.logger.warning(f"[NETWORK] request_state_all error: {e}")
