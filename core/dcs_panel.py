# -*- coding: utf-8 -*-
"""Painel simples que lê panel_status.json e renderiza um resumo no terminal.
Executar como módulo (na raiz do projeto): python -m core.dcs_panel
"""
import os, time, json
from datetime import datetime

BASE = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
PANEL_PATH = os.path.join(LOG_DIR, 'panel_status.json')

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def render(data: dict):
    clear()
    print('DCs.AI — Painel de Status (vFinal)')
    print('=================================')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'Atualizado: {now}\n')

    modules = sorted(data.items())
    for name, info in modules:
        if isinstance(info, dict):
            status = info.get('status', 'unknown')
            last = info.get('last_update', '')
            cpu = info.get('cpu_percent', None)
            mem = info.get('mem_percent', None)
            proc = info.get('process_count', None)
            line = f'- {name}: status={status}'
            if cpu is not None:
                line += f' | CPU={cpu}%'
            if mem is not None:
                line += f' | MEM={mem}%'
            if proc is not None:
                line += f' | PROC={proc}'
            line += f' | last={last}'
            print(line)
        else:
            print(f'- {name}: {repr(info)}')
    print('\n(Pressione Ctrl+C para sair)')

def main(poll_interval: float = 1.0):
    if not os.path.exists(PANEL_PATH):
        with open(PANEL_PATH, 'w', encoding='utf-8') as f:
            json.dump({'startup': {'status': 'waiting', 'last_update': datetime.now().isoformat()}}, f)
    try:
        while True:
            try:
                with open(PANEL_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {'error': 'could not read panel_status.json'}
            render(data)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print('\nPainel encerrado pelo usuário.')

if __name__ == '__main__':
    main()
