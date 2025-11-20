# -*- coding: utf-8 -*-
"""DCs.AI - Core entrypoint (starts monitor and autocorrect modules).
Run with: python dcs_main.py
"""
import os
import sys
import threading
import time
from datetime import datetime
from core import dcs_network_v2
from core.dcs_monitor import DCSMonitor
from core.dcs_autocorrect import DCSAutoCorrect
from core.dcs_state_sync import StateSync

state_sync = StateSync(interval=20)   # a cada 20s
state_sync.start()

# --- Inicia rede (Fase 114) ---
from core import dcs_network_v2

# start server in background
threading.Thread(target=dcs_network_v2.start_server, kwargs={"bind_port": 22000}, daemon=True).start()

# optionally connect to known peers from config
known_peers = [("127.0.0.1", 22001)]
for h, p in known_peers:
    threading.Thread(target=dcs_network_v2.connect_and_handshake, args=(h, p), daemon=True).start()


# --- Configuração de diretórios e logs ---
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

LOG_DIR = os.path.join(ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LAUNCH_LOG = os.path.join(LOG_DIR, 'dcs_log.txt')


def write_launch(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LAUNCH_LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {msg}\n')
    print(msg)


# --- Importa módulos principais ---
try:
    from core.dcs_monitor import DCSMonitor
    from core.dcs_autocorrect import DCSAutoCorrect
except Exception as e:
    write_launch(f'ERROR importing core modules: {e}')
    raise


# --- Função principal ---
def run_core():
    write_launch('Starting DCs.AI core...')
    monitor = DCSMonitor()
    autocorrect = DCSAutoCorrect()

    t_monitor = threading.Thread(target=monitor.start, kwargs={'interval': 1.0, 'cycles': 0}, daemon=True)
    t_autocorrect = threading.Thread(target=autocorrect.start, kwargs={'cycles': 3, 'delay': 2.0}, daemon=True)

    t_monitor.start()
    t_autocorrect.start()

    write_launch('Modules started. Press Ctrl+C to stop.')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        write_launch('Shutting down modules...')
        monitor.stop()
        autocorrect.stop()
        t_monitor.join(timeout=2)
        t_autocorrect.join(timeout=2)
        write_launch('Shutdown complete.')


if __name__ == '__main__':
    run_core()
