# -*- coding: utf-8 -*-
"""DCSMonitor - writes panel_status.json periodically with CPU/MEM (uses psutil if available)."""
import os, time, json
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
LOG_DIR = os.path.join(ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
PANEL_PATH = os.path.join(ROOT, 'data', 'panel_status.json')
os.makedirs(os.path.dirname(PANEL_PATH), exist_ok=True)

try:
    import psutil
except Exception:
    psutil = None

class DCSMonitor:
    def __init__(self):
        self.name = 'monitor'
        self.running = False

    def _update_panel(self, payload):
        data = {}
        try:
            if os.path.exists(PANEL_PATH):
                with open(PANEL_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
        except Exception:
            data = {}
        data[self.name] = payload
        with open(PANEL_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def start(self, interval: float = 1.0, cycles: int = 0):
        self.running = True
        i = 0
        while self.running and (cycles == 0 or i < cycles):
            i += 1
            if psutil:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                try:
                    temp = psutil.sensors_temperatures()
                    if temp:
                        first = next(iter(temp.values()))[0].current
                        temp_val = round(first, 1)
                    else:
                        temp_val = None
                except Exception:
                    temp_val = None
            else:
                cpu = round((i * 7) % 100, 1)
                mem = round(30 + (i * 3) % 60, 1)
                temp_val = None

            payload = {
                'status': 'running',
                'cpu_percent': cpu,
                'mem_percent': mem,
                'temp': temp_val,
                'last_update': datetime.now().isoformat()
            }
            self._update_panel(payload)
            time.sleep(interval)

        self._update_panel({'status': 'idle', 'last_update': datetime.now().isoformat()})
        self.running = False

    def stop(self):
        self.running = False
