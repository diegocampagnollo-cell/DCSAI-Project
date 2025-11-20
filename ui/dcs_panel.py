# -*- coding: utf-8 -*-
"""DCs.AI - Painel Vivo (Cyber Blue Final)
Tkinter GUI reading core/logs/panel_status.json. Shows real stats when psutil installed.
Run from project root:
    python -m ui.dcs_panel
""" 
import os, json, time
from datetime import datetime
try:
    import tkinter as tk
except Exception:
    print('Tkinter não disponível. Instale/execute em sistema com Tk support.')
    raise

LOGS = os.path.join(os.path.dirname(__file__), '..', 'core', 'logs')
PANEL_PATH = os.path.join(LOGS, 'panel_status.json')
LOG_FILE = os.path.join(LOGS, 'dcs_log.txt')

def safe_load():
    try:
        with open(PANEL_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

class Neon(tk.Label):
    def __init__(self, master, text='', **kw):
        kw.setdefault('bg','#000000'); kw.setdefault('fg','#00e6ff'); kw.setdefault('font',('Consolas',12,'bold'))
        super().__init__(master, text=text, **kw)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DCs.AI - Painel Vivo')
        self.configure(bg='#000000')
        self.geometry('620x180')
        self.resizable(False, False)

        header = tk.Label(self, text='DCs.AI – Painel Vivo', bg='#000000', fg='#00e6ff', font=('Consolas',14,'bold'))
        header.pack(pady=(8,4))

        frame = tk.Frame(self, bg='#000000')
        frame.pack()

        self.cpu = Neon(frame, text='⚙ CPU: -- %'); self.cpu.grid(row=0,column=0,padx=10,pady=4,sticky='w')
        self.mem = Neon(frame, text='🧠 MEM: -- %'); self.mem.grid(row=0,column=1,padx=10,pady=4,sticky='w')
        self.proc = Neon(frame, text='⚡ PROCS: --'); self.proc.grid(row=1,column=0,padx=10,pady=4,sticky='w')
        self.temp = Neon(frame, text='🌡️ TEMP: -- °C'); self.temp.grid(row=1,column=1,padx=10,pady=4,sticky='w')

        btns = tk.Frame(self, bg='#000000')
        btns.pack(pady=(6,10))
        self.paused = False
        self.btn_pause = tk.Button(btns, text='Pausar', width=10, command=self.toggle, bg='#00121a', fg='#00e6ff')
        self.btn_pause.pack(side='left', padx=6)
        self.btn_quit = tk.Button(btns, text='Encerrar', width=10, command=self.quit, bg='#00121a', fg='#00e6ff')
        self.btn_quit.pack(side='left', padx=6)

        self.after(500, self.loop)

    def toggle(self):
        self.paused = not self.paused
        self.btn_pause.config(text='Retomar' if self.paused else 'Pausar')

    def loop(self):
        if not self.paused:
            data = safe_load()
            mon = data.get('dcs_monitor') if isinstance(data, dict) else None
            ac = data.get('dcs_autocorrect') if isinstance(data, dict) else None

            cpu = mon.get('cpu_percent') if mon else None
            mem = mon.get('mem_percent') if mon else None
            procs = mon.get('procs') if mon else None
            temp = mon.get('temperature') if mon else None

            self.cpu.config(text=f'⚙ CPU: {cpu if cpu is not None else "--"} %')
            self.mem.config(text=f'🧠 MEM: {mem if mem is not None else "--"} %')
            self.proc.config(text=f'⚡ PROCS: {procs if procs is not None else "--"}')
            self.temp.config(text=f'🌡️ TEMP: {temp if temp is not None else "--"} °C')
        self.after(900, self.loop)

if __name__ == '__main__':
    app = App()
    app.mainloop()
