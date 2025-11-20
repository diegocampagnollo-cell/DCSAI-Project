# -*- coding: utf-8 -*-
"""
StateSync - periodically push state to peers
"""

import json
import socket
import threading
import time

class StateSync:
    def __init__(self, interval=20, peers=None):
        self.interval = interval
        self.peers = peers or [("127.0.0.1", 22000)]
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[SYNC] StateSync started")

    def stop(self):
        self.running = False
        print("[SYNC] StateSync stopped")

    def _loop(self):
        while self.running:
            for host, port in list(self.peers):
                self._push_state(host, port)
            time.sleep(self.interval)

    def _push_state(self, host, port):
        try:
            s = socket.create_connection((host, int(port)), timeout=4)
            payload = {"type":"STATE_PUSH", "state": self._local_state(), "ts": int(time.time())}
            s.sendall((json.dumps(payload) + "\n").encode('utf-8'))
            s.close()
            print(f"[SYNC] Pushed state to {host}:{port}")
        except Exception as e:
            print(f"[SYNC] Push error to {host}:{port}: {e}")

    def _local_state(self):
        return {
            "timestamp": int(time.time()),
            "modules": ["monitor","autocorrect"],
            "version": "DCs_AI_vFinal"
        }
