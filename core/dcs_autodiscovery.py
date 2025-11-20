# -*- coding: utf-8 -*-
"""
core/dcs_autodiscovery.py — Fase 116.3.9.1
Sistema híbrido de descoberta automática entre nós DCS.AI.
Broadcast UDP + escuta de peers + cache local.

API pública:
- start()
- stop()
- register_peer_listener(fn)
- get_peers()
"""

import socket
import threading
import json
import time
import traceback

UDP_PORT = 23000
BEACON_INTERVAL = 3.0

class AutoDiscovery:
    def __init__(self, ident="core", port_hint=22000):
        self.ident = ident
        self.port_hint = port_hint
        self.running = False
        self.peers = {}
        self._lock = threading.Lock()
        self._thread_tx = None
        self._thread_rx = None
        self._listeners = []

    # ---------------- registration ----------------
    def register_peer_listener(self, fn):
        """Registra função callback(peer_addr, info_dict)."""
        if callable(fn):
            self._listeners.append(fn)

    def _notify_listeners(self, peer, info):
        for fn in self._listeners:
            try:
                fn(peer, info)
            except Exception:
                traceback.print_exc()

    # ---------------- beacon send ----------------
    def _beacon_tx(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({
            "ident": self.ident,
            "port": self.port_hint,
            "time": time.time()
        }).encode("utf-8")

        while self.running:
            try:
                sock.sendto(msg, ("255.255.255.255", UDP_PORT))
            except Exception:
                traceback.print_exc()
            time.sleep(BEACON_INTERVAL)
        sock.close()

    # ---------------- beacon receive ----------------
    def _beacon_rx(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))
        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                if not data:
                    continue
                info = json.loads(data.decode("utf-8"))
                if addr[0] == "127.0.0.1":
                    continue  # ignora self
                with self._lock:
                    self.peers[addr[0]] = {
                        "port": info.get("port"),
                        "last_seen": time.time(),
                        "ident": info.get("ident")
                    }
                self._notify_listeners(addr, info)
            except socket.timeout:
                continue
            except Exception:
                traceback.print_exc()
        sock.close()

    # ---------------- lifecycle ----------------
    def start(self):
        if self.running:
            return
        self.running = True
        self._thread_tx = threading.Thread(target=self._beacon_tx, daemon=True)
        self._thread_rx = threading.Thread(target=self._beacon_rx, daemon=True)
        self._thread_tx.start()
        self._thread_rx.start()

    def stop(self):
        self.running = False

    def get_peers(self):
        """Retorna snapshot atual dos peers detectados."""
        with self._lock:
            return dict(self.peers)
