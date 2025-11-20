# rpc_panel_gui.py
# DCs.AI Cyber Panel+ (Fase 116.5)
# Requires: customtkinter (mandatory), ttkbootstrap (optional)
# Run: python rpc_panel_gui.py

"""
Painel GUI moderno com suporte ao backend RPC assíncrono.
- Usa customtkinter para a GUI.
- Usa ttkbootstrap se disponível para controls extras (opcional).
- Inicia um loop asyncio em thread separada para comunicação.
- Conecta no host/port configuráveis e mostra logs em tempo real.
- Novo: define DCS_RPC_TOKEN automaticamente se ausente.
- Novo: botão “Restart Core” envia {"type":"request","method":"restart"}.
"""

import os
import time
import json
import asyncio
import threading
import queue
from datetime import datetime

try:
    import customtkinter as ctk
except Exception as e:
    raise SystemExit("customtkinter não encontrado. Instale: pip install customtkinter")

try:
    import ttkbootstrap as tb # pyright: ignore[reportMissingImports]
    HAS_TTB = True
except Exception:
    HAS_TTB = False

# Configs
DEFAULT_HOST = os.environ.get("DCS_RPC_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("DCS_RPC_PORT", "22888"))
AUTH_TOKEN = os.environ.get("DCS_RPC_TOKEN") or "panel_token"
os.environ["DCS_RPC_TOKEN"] = AUTH_TOKEN  # garante que sempre exista

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def ts():
    return datetime.now().strftime("%H:%M:%S")

class RPCClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=AUTH_TOKEN, log_cb=None, event_cb=None):
        self.host = host
        self.port = port
        self.token = token
        self.log_cb = log_cb or (lambda m, lvl='INFO': None)
        self.event_cb = event_cb or (lambda ev, d: None)
        self.reader = None
        self.writer = None
        self._connected = False
        self._task = None
        self._loop = None

    async def connect(self):
        try:
            self.log(f"Connecting to {self.host}:{self.port}...", 'INFO')
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self._connected = True
            self.log("Connected ✅", 'INFO')
            auth = {"type": "auth", "token": self.token}
            await self._send(auth)
            await self._reader_loop()
        except Exception as e:
            self.log(f"Connection failed: {e}", 'ERROR')
            self._connected = False
            raise

    async def _reader_loop(self):
        try:
            while True:
                line = await self.reader.readline()
                if not line:
                    self.log("Connection closed by remote", 'WARN')
                    self._connected = False
                    self.event_cb('disconnected', None)
                    break
                try:
                    data = json.loads(line.decode().strip())
                except Exception:
                    data = line.decode(errors='ignore').strip()
                self.log(f"RX {data}", 'RX')
                if isinstance(data, dict) and data.get('type') in ('response', 'notification', 'request'):
                    self.event_cb(data.get('method') or data.get('type') or 'message', data)
                else:
                    self.event_cb('raw', data)
        except asyncio.CancelledError:
            self.log('Reader loop cancelled', 'DEBUG')
        except Exception as e:
            self.log(f"Reader loop error: {e}", 'ERROR')
            self._connected = False
            self.event_cb('disconnected', None)

    async def _send(self, payload: dict):
        if not self._connected or not self.writer:
            raise ConnectionError('Not connected')
        text = json.dumps(payload, ensure_ascii=False) + "\n"
        self.writer.write(text.encode('utf-8'))
        await self.writer.drain()
        self.log(f"TX {payload}", 'TX')

    def send_async(self, payload: dict):
        if not self._loop:
            raise RuntimeError('Client not started')
        return asyncio.run_coroutine_threadsafe(self._send(payload), self._loop)

    def start_in_loop(self, loop):
        self._loop = loop
        self._task = asyncio.run_coroutine_threadsafe(self.connect(), loop)

    def stop(self):
        try:
            if self._task and not self._task.done():
                self._task.cancel()
        except Exception:
            pass
        try:
            if self.writer:
                self.writer.close()
        except Exception:
            pass
        self._connected = False
        self.log('Client stopped', 'INFO')

    def log(self, message, level='INFO'):
        if callable(self.log_cb):
            self.log_cb(f"[{ts()}] {message}", level)

class PanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ DCs.AI Cyber Panel+")
        self.geometry("980x640")
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()
        self.rpc = RPCClient(log_cb=self._log, event_cb=self._event)
        self.ping_count = 0
        self._build_ui()
        self._ui_q = queue.Queue()
        self.after(100, self._process_ui_queue)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _build_ui(self):
        header = ctk.CTkFrame(self)
        header.pack(fill='x', padx=12, pady=8)
        ctk.CTkLabel(header, text='DCs.AI Cyber Panel+', font=('Consolas', 20, 'bold')).pack(side='left', padx=(6,12))
        self.status_var = ctk.StringVar(value='Desconectado')
        self.status_lbl = ctk.CTkLabel(header, textvariable=self.status_var, width=140)
        self.status_lbl.pack(side='right', padx=8)

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(fill='x', padx=12, pady=(0,8))

        self.host_entry = ctk.CTkEntry(ctrl, placeholder_text='Host', width=180)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.pack(side='left', padx=8, pady=8)

        self.port_entry = ctk.CTkEntry(ctrl, placeholder_text='Port', width=120)
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.port_entry.pack(side='left', padx=8, pady=8)

        self.btn_connect = ctk.CTkButton(ctrl, text='Conectar', command=self._on_connect, width=110)
        self.btn_disconnect = ctk.CTkButton(ctrl, text='Desconectar', command=self._on_disconnect, width=110)
        self.btn_connect.pack(side='left', padx=6)
        self.btn_disconnect.pack(side='left', padx=6)

        self.ping_lbl = ctk.CTkLabel(ctrl, text=f'Pings: {self.ping_count}', width=100)
        self.ping_lbl.pack(side='left', padx=12)

        # Botões de ação (Ping + Restart)
        action_frame = ctk.CTkFrame(ctrl)
        action_frame.pack(side='right')
        self.btn_restart = ctk.CTkButton(action_frame, text='Restart Core', fg_color='#FF5500', command=self._on_restart)
        self.btn_restart.pack(side='right', padx=8)
        self.btn_ping = ctk.CTkButton(action_frame, text='Ping → Core', fg_color='#0088FF', command=self._on_ping)
        self.btn_ping.pack(side='right', padx=8)

        self.logbox = ctk.CTkTextbox(self, width=940, height=420)
        self.logbox.pack(padx=12, pady=(0,12))
        self.logbox.insert('end', '🟢 Painel iniciado.\n')

        bottom = ctk.CTkFrame(self)
        bottom.pack(fill='x', padx=12, pady=(0,12))
        self.cmd_entry = ctk.CTkEntry(bottom, placeholder_text='Comando / payload JSON (ex: {"cmd":"restart"})')
        self.cmd_entry.pack(side='left', fill='x', expand=True, padx=8)
        self.btn_send = ctk.CTkButton(bottom, text='Enviar', command=self._on_send_cmd)
        self.btn_send.pack(side='left', padx=8)
        self.btn_clear = ctk.CTkButton(bottom, text='Limpar', command=self._clear_logs)
        self.btn_clear.pack(side='left', padx=8)

    def _enqueue_ui(self, fn, *a, **k):
        self._ui_q.put((fn, a, k))

    def _process_ui_queue(self):
        try:
            while True:
                fn, a, k = self._ui_q.get_nowait()
                fn(*a, **k)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_ui_queue)

    def _set_status(self, text, color=None):
        self.status_var.set(text)
        if color:
            try:
                self.status_lbl.configure(text_color=color)
            except Exception:
                pass

    def _log(self, message, level='INFO'):
        self._enqueue_ui(self._append_log, message, level)

    def _append_log(self, message, level='INFO'):
        prefix = {'INFO': 'ℹ️', 'WARN': '⚠️', 'ERROR': '❌', 'RX': '◀️', 'TX': '▶️', 'DEBUG': '🐞'}.get(level, '')
        self.logbox.insert('end', f"{prefix} {message}\n")
        self.logbox.see('end')

    def _event(self, ev, data):
        self._enqueue_ui(self._handle_event, ev, data)

    def _handle_event(self, ev, data):
        if ev == 'disconnected':
            self._set_status('Desconectado', '#FF5555')
        elif ev in ('ping', 'pong', 'ping_result'):
            self.ping_count += 1
            self.ping_lbl.configure(text=f'Pings: {self.ping_count}')
            self._append_log(f"Ping result: {data}", 'INFO')
        elif ev == 'raw':
            self._append_log(f"Raw: {data}", 'DEBUG')
        else:
            self._append_log(f"Notification from core: {ev} {data}", 'INFO')

    def _on_connect(self):
        host = self.host_entry.get().strip() or DEFAULT_HOST
        try:
            port = int(self.port_entry.get().strip())
        except Exception:
            port = DEFAULT_PORT
        self.rpc.host = host
        self.rpc.port = port
        self._set_status('Conectando...', '#FFFF00')
        try:
            self.rpc.start_in_loop(self.loop)
            self._set_status('Conectado (aguardando auth)', '#00FF88')
        except Exception as e:
            self._set_status('Erro', '#FF5555')
            self._append_log(f'Erro iniciando conexão: {e}', 'ERROR')

    def _on_disconnect(self):
        try:
            self.rpc.stop()
            self._set_status('Desconectado', '#FF5555')
        except Exception as e:
            self._append_log(f'Desconectar erro: {e}', 'ERROR')

    def _on_ping(self):
        payload = {"type": "request", "method": "ping", "id": int(time.time())}
        try:
            self.rpc.send_async(payload)
        except Exception as e:
            self._append_log(f'Ping falhou: {e}', 'ERROR')

    def _on_restart(self):
        payload = {"type": "request", "method": "restart", "id": int(time.time())}
        try:
            self.rpc.send_async(payload)
            self._append_log('Comando de restart enviado.', 'INFO')
        except Exception as e:
            self._append_log(f'Restart falhou: {e}', 'ERROR')

    def _on_send_cmd(self):
        txt = self.cmd_entry.get().strip()
        if not txt:
            return
        try:
            payload = json.loads(txt)
        except Exception:
            payload = {"type": "command", "cmd": txt}
        try:
            self.rpc.send_async(payload)
        except Exception as e:
            self._append_log(f'Enviar falhou: {e}', 'ERROR')

    def _clear_logs(self):
        self.logbox.delete('1.0', 'end')
        self._append_log('Logs limpos.', 'INFO')

if __name__ == '__main__':
    app = PanelApp()
    app.mainloop()
