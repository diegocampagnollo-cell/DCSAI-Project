# rpc_panel_gui_cyber_reconnect.py
# DCs.AI Cyber Panel — Radar Pulse + Auto-Reconnect (Fase 116.6+)
# Run: python rpc_panel_gui_cyber_reconnect.py

import os
import time
import json
import asyncio
import threading
import queue
import math
import random
from datetime import datetime
from typing import Any, Dict

# UI libs
try:
    import customtkinter as ctk
except Exception:
    raise SystemExit("customtkinter não encontrado. Instale: pip install customtkinter")

# optional libs
try:
    import ttkbootstrap as tb
    HAS_TTB = True
except Exception:
    HAS_TTB = False

try:
    import psutil # type: ignore
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False

# ----------------------------------------------------------
# Config
# ----------------------------------------------------------
DEFAULT_HOST = os.environ.get("DCS_RPC_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("DCS_RPC_PORT", "22888"))
AUTH_TOKEN = os.environ.get("DCS_RPC_TOKEN") or "panel_token"
os.environ["DCS_RPC_TOKEN"] = AUTH_TOKEN

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def ts():
    return datetime.now().strftime("%H:%M:%S")

# ----------------------------------------------------------
# Lightweight RPC client (async) — integrates with your core
# ----------------------------------------------------------
class RPCClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=AUTH_TOKEN, log_cb=None, event_cb=None):
        self.host = host
        self.port = port
        self.token = token
        self.log_cb = log_cb or (lambda m, lvl='INFO': None)
        self.event_cb = event_cb or (lambda ev, d: None)
        self._reader = None
        self._writer = None
        self._connected = False
        self._loop = None
        self._task = None
        self._stop = False

    def log(self, message, level='INFO'):
        self.log_cb(f"[{ts()}] {message}", level)

    async def _reader_loop(self):
        try:
            while not self._stop:
                line = await self._reader.readline()
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
                if isinstance(data, dict):
                    method = data.get('method') or data.get('type') or data.get('event')
                    self.event_cb(method or 'message', data)
                else:
                    self.event_cb('raw', data)
        except asyncio.CancelledError:
            self.log("Reader loop cancelled", 'DEBUG')
        except Exception as e:
            self.log(f"Reader loop error: {e}", 'ERROR')
            self._connected = False
            self.event_cb('disconnected', None)

    async def connect(self):
        try:
            self.log(f"Trying {self.host}:{self.port}...", 'INFO')
            self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
            self._connected = True
            self.log("Connected ✅", 'INFO')
            # send auth token if protocol expects it
            auth = {"type": "auth", "token": self.token}
            await self._send(auth)
            await self._reader_loop()
        except Exception as e:
            self.log(f"Connection failed: {e}", 'ERROR')
            self._connected = False
            raise

    async def _send(self, payload: Dict[str, Any]):
        if not self._connected or not self._writer:
            raise ConnectionError("Not connected")
        text = json.dumps(payload, ensure_ascii=False) + "\n"
        self._writer.write(text.encode('utf-8'))
        await self._writer.drain()
        self.log(f"TX {payload}", 'TX')

    def start_in_loop(self, loop):
        if self._loop is not None:
            return
        self._loop = loop
        self._stop = False
        self._task = asyncio.run_coroutine_threadsafe(self.connect(), loop)

    def stop(self):
        self._stop = True
        try:
            if self._task and not self._task.done():
                self._task.cancel()
        except Exception:
            pass
        try:
            if self._writer:
                self._writer.close()
        except Exception:
            pass
        self._connected = False
        self.log("Client stopped", 'INFO')

    def send_async(self, payload: Dict[str, Any]):
        if not self._loop:
            raise RuntimeError("Client loop not started")
        return asyncio.run_coroutine_threadsafe(self._send(payload), self._loop)

# ----------------------------------------------------------
# Radar Canvas (same as before)
# ----------------------------------------------------------
class RadarCanvas(ctk.CTkCanvas):
    def __init__(self, master, width=420, height=420, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, **kwargs)
        self.width = width; self.height = height
        self.center = (width // 2, height // 2)
        self.radius = min(width, height) // 2 - 10
        self.angle = 0.0
        self.metric = 0.0
        self._anim_running = False
        self._bg = "#071024"
        self.configure(bg=self._bg)
        self._draw_static()

    def _draw_static(self):
        self.delete("all")
        cx, cy = self.center
        for i in range(6, 0, -1):
            r = int(self.radius * (i/6.0))
            self.create_oval(cx-r, cy-r, cx+r, cy+r, outline="", fill="", tags="glow"+str(i))
        for i in range(1,5):
            r = int(self.radius * (i/5.0))
            self.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#16324C", width=1)
        self.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#00FFAA", outline="")

    def _draw_frame(self):
        self.delete("pulse")
        cx, cy = self.center
        a = math.radians(self.angle)
        x = cx + math.cos(a) * self.radius
        y = cy + math.sin(a) * self.radius
        angle_width = math.radians(6)
        a1 = a - angle_width; a2 = a + angle_width
        x1 = cx + math.cos(a1) * self.radius; y1 = cy + math.sin(a1) * self.radius
        x2 = cx + math.cos(a2) * self.radius; y2 = cy + math.sin(a2) * self.radius
        self.create_polygon(cx, cy, x1, y1, x, y, x2, y2,
                            fill="#00B3FF", stipple="gray50", outline="", tags="pulse")
        blip_r = int(8 + (self.metric * 18))
        bx = cx + math.cos(a) * (self.radius * (0.3 + 0.6 * self.metric))
        by = cy + math.sin(a) * (self.radius * (0.3 + 0.6 * self.metric))
        self.create_oval(bx-blip_r, by-blip_r, bx+blip_r, by+blip_r,
                         fill="#00FFAA", outline="", tags="pulse")

    def start_anim(self):
        if self._anim_running: return
        self._anim_running = True; self._animate()

    def stop_anim(self):
        self._anim_running = False

    def _animate(self):
        if not self._anim_running: return
        self.angle = (self.angle + 4.0 + (self.metric * 0.6)) % 360.0
        self._draw_frame()
        self.after(40, self._animate)

    def set_metric(self, value: float):
        self.metric = max(0.0, min(1.0, value))

# ----------------------------------------------------------
# Panel App with Auto-Reconnect manager
# ----------------------------------------------------------
class PanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ DCs.AI Cyber Panel — Auto-Reconnect")
        self.geometry("1100x720")
        self.minsize(980, 640)

        self._ui_q = queue.Queue()
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()

        self.rpc = RPCClient(log_cb=self._log_callback, event_cb=self._on_event)
        self.ping_count = 0

        # Auto-reconnect config/state
        self.auto_reconnect = True
        self.base_delay = 2.0
        self.max_backoff = 30.0
        self._reconnect_thread = threading.Thread(target=self._reconnect_manager, daemon=True)
        self._reconnect_thread.start()

        self._build_ui()
        self.after(100, self._process_ui_queue)
        self._sim_running = True
        self.after(1200, self._simulate_if_disconnected)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="#071124", corner_radius=0)
        header.pack(fill='x', padx=8, pady=8)
        ctk.CTkLabel(header, text="DCs.AI Cyber Panel", font=("Consolas", 22, "bold"), text_color="#00FFD1").pack(side='left', padx=12)
        self.status_var = ctk.StringVar(value="Desconectado")
        self.status_lbl = ctk.CTkLabel(header, textvariable=self.status_var, width=200)
        self.status_lbl.pack(side='right', padx=12)

        main = ctk.CTkFrame(self)
        main.pack(fill='both', expand=True, padx=12, pady=(0,12))

        left = ctk.CTkFrame(main); left.pack(side='left', fill='both', expand=False, padx=(0,8), pady=8)
        self.radar = RadarCanvas(left, width=500, height=500); self.radar.pack(padx=6, pady=6)
        self.radar.start_anim()
        metric_frame = ctk.CTkFrame(left); metric_frame.pack(fill='x', padx=6, pady=6)
        self.cpu_var = ctk.StringVar(value="CPU: -- %"); self.mem_var = ctk.StringVar(value="RAM: -- %"); self.uptime_var = ctk.StringVar(value="Uptime: --")
        ctk.CTkLabel(metric_frame, textvariable=self.cpu_var).pack(anchor='w', padx=6)
        ctk.CTkLabel(metric_frame, textvariable=self.mem_var).pack(anchor='w', padx=6)
        ctk.CTkLabel(metric_frame, textvariable=self.uptime_var).pack(anchor='w', padx=6)

        right = ctk.CTkFrame(main); right.pack(side='right', fill='both', expand=True, padx=(8,0), pady=8)
        ctrl = ctk.CTkFrame(right); ctrl.pack(fill='x', padx=6, pady=6)
        self.host_entry = ctk.CTkEntry(ctrl, placeholder_text='Host', width=180); self.host_entry.insert(0, DEFAULT_HOST); self.host_entry.pack(side='left', padx=6)
        self.port_entry = ctk.CTkEntry(ctrl, placeholder_text='Port', width=110); self.port_entry.insert(0, str(DEFAULT_PORT)); self.port_entry.pack(side='left', padx=6)
        self.btn_connect = ctk.CTkButton(ctrl, text='Connect', width=110, command=self._on_connect); self.btn_connect.pack(side='left', padx=6)
        self.btn_disconnect = ctk.CTkButton(ctrl, text='Disconnect', width=110, command=self._on_disconnect); self.btn_disconnect.pack(side='left', padx=6)

        # AutoReconnect controls
        ar_frame = ctk.CTkFrame(right); ar_frame.pack(fill='x', padx=6, pady=6)
        self.auto_var = ctk.BooleanVar(value=self.auto_reconnect)
        self.chk_auto = ctk.CTkCheckBox(ar_frame, text='Auto-Reconnect', variable=self.auto_var, command=self._on_toggle_auto)
        self.chk_auto.pack(side='left', padx=6)
        self.base_delay_entry = ctk.CTkEntry(ar_frame, width=80, placeholder_text='base s')
        self.base_delay_entry.insert(0, str(self.base_delay)); self.base_delay_entry.pack(side='left', padx=6)
        self.max_backoff_entry = ctk.CTkEntry(ar_frame, width=100, placeholder_text='max s')
        self.max_backoff_entry.insert(0, str(self.max_backoff)); self.max_backoff_entry.pack(side='left', padx=6)

        act = ctk.CTkFrame(right); act.pack(fill='x', padx=6, pady=6)
        self.btn_ping = ctk.CTkButton(act, text='Ping → Core', fg_color="#0088FF", command=self._on_ping); self.btn_ping.pack(side='left', padx=6)
        self.btn_restart = ctk.CTkButton(act, text='Restart Core', fg_color="#FF6A00", command=self._on_restart); self.btn_restart.pack(side='left', padx=6)
        self.btn_clear = ctk.CTkButton(act, text='Clear Logs', fg_color="#555555", command=self._clear_logs); self.btn_clear.pack(side='left', padx=6)

        self.logbox = ctk.CTkTextbox(right, width=420, height=420); self.logbox.pack(padx=6, pady=(8,6), fill='both', expand=True)
        self._append_log("🟢 Panel started.", 'INFO')

    # UI queue helpers
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

    def _append_log(self, message, level='INFO'):
        prefix = {'INFO': 'ℹ️', 'WARN': '⚠️', 'ERROR': '❌', 'RX': '◀️', 'TX': '▶️', 'DEBUG': '🐞'}.get(level, '')
        self.logbox.insert('end', f"{prefix} [{ts()}] {message}\n")
        self.logbox.see('end')

    def _log_callback(self, message, level='INFO'):
        self._enqueue_ui(self._append_log, message, level)

    def _on_event(self, ev, data):
        self._enqueue_ui(self._handle_event, ev, data)

    def _handle_event(self, ev, data):
        if ev in ('disconnected', None):
            self._set_status("Desconectado", "#FF5555")
        elif ev in ('connected',):
            self._set_status("Conectado", "#00FF88")
        elif ev in ('state_update', 'sysinfo', 'status'):
            payload = data.get('params') if isinstance(data, dict) and data.get('params') else data
            cpu = payload.get('cpu') if isinstance(payload, dict) else None
            ram = payload.get('ram') if isinstance(payload, dict) else None
            uptime = payload.get('uptime') if isinstance(payload, dict) else None
            cpu_v = float(cpu) if cpu is not None else 0.0
            mem_v = float(ram) if ram is not None else 0.0
            self.cpu_var.set(f"CPU: {cpu_v:.1f} %"); self.mem_var.set(f"RAM: {mem_v:.1f} %"); self.uptime_var.set(f"Uptime: {uptime or '--'}")
            metric = max(0.0, min(1.0, cpu_v / 100.0))
            self.radar.set_metric(metric)
            self._append_log(f"Received state: cpu={cpu_v} mem={mem_v}", 'INFO')
        elif ev == 'ping_result' or (isinstance(data, dict) and data.get('method') == 'ping'):
            self._append_log(f"Ping result: {data}", 'INFO')
        else:
            self._append_log(f"Event {ev}: {data}", 'DEBUG')

    def _set_status(self, text, color=None):
        self.status_var.set(text)
        try:
            if color:
                self.status_lbl.configure(text_color=color)
        except Exception:
            pass

    # Controls
    def _on_connect(self):
        host = self.host_entry.get().strip() or DEFAULT_HOST
        try:
            port = int(self.port_entry.get().strip())
        except Exception:
            port = DEFAULT_PORT
        self.rpc.host = host; self.rpc.port = port
        self._set_status("Conectando...", "#FFFF00")
        try:
            # start RPC client on event loop
            self.rpc.start_in_loop(self.loop)
            self._set_status("Conectado (aguardando auth)", "#00FF88")
            self._append_log("Manual connect requested", 'INFO')
        except Exception as e:
            self._append_log(f"Erro iniciando conexão: {e}", 'ERROR'); self._set_status("Erro", "#FF5555")

    def _on_disconnect(self):
        try:
            self.rpc.stop(); self._set_status("Desconectado", "#FF5555"); self._append_log("Disconnected by user", 'WARN')
        except Exception as e:
            self._append_log(f"Desconectar erro: {e}", 'ERROR')

    def _on_ping(self):
        payload = {"type": "request", "method": "ping", "id": int(time.time())}
        try:
            self.rpc.send_async(payload)
        except Exception as e:
            self._append_log(f"Ping falhou: {e}", 'ERROR')

    def _on_restart(self):
        payload = {"type": "request", "method": "restart", "id": int(time.time())}
        try:
            self.rpc.send_async(payload); self._append_log("Restart command sent", 'INFO')
        except Exception as e:
            self._append_log(f"Restart falhou: {e}", 'ERROR')

    def _clear_logs(self):
        self.logbox.delete('1.0', 'end'); self._append_log("Logs limpos", 'INFO')

    # Auto-Reconnect toggle handler
    def _on_toggle_auto(self):
        self.auto_reconnect = bool(self.auto_var.get())
        self._append_log(f"Auto-Reconnect {'enabled' if self.auto_reconnect else 'disabled'}", 'INFO')

    # -------------------------
    # Reconnect manager (thread)
    # -------------------------
    def _reconnect_manager(self):
        """Thread that attempts reconnections with exponential backoff and jitter."""
        backoff = self.base_delay
        while True:
            try:
                # read current config values from UI
                try:
                    base_val = float(self.base_delay_entry.get().strip())
                    max_val = float(self.max_backoff_entry.get().strip())
                    self.base_delay = max(0.1, base_val)
                    self.max_backoff = max(1.0, max_val)
                except Exception:
                    pass

                if self.auto_reconnect and not getattr(self.rpc, "_connected", False):
                    # attempt connect
                    self._enqueue_ui(self._append_log, f"Auto-Reconnect: tentando conectar (backoff={backoff:.1f}s)", 'INFO')
                    try:
                        # schedule connect in the rpc loop
                        if not self.rpc._loop:
                            # ensure loop started
                            pass
                        # call start_in_loop -> it schedules the connect coroutine
                        self.rpc.start_in_loop(self.loop)
                        # wait a short while for connection to establish
                        # poll for status up to base_delay seconds
                        wait = 0.0
                        poll_interval = 0.2
                        succeeded = False
                        while wait < (backoff + 1.0):
                            if getattr(self.rpc, "_connected", False):
                                succeeded = True
                                break
                            time.sleep(poll_interval); wait += poll_interval
                        if succeeded:
                            self._enqueue_ui(self._append_log, "Auto-Reconnect: conectado com sucesso.", 'INFO')
                            backoff = self.base_delay  # reset backoff on success
                        else:
                            # failed: increase backoff
                            self._enqueue_ui(self._append_log, f"Auto-Reconnect: tentativa falhou, aumentando backoff.", 'WARN')
                            backoff = min(self.max_backoff, backoff * 2.0 + random.uniform(0, 1.0))
                            time.sleep(backoff)
                    except Exception as e:
                        self._enqueue_ui(self._append_log, f"Auto-Reconnect error: {e}", 'ERROR')
                        backoff = min(self.max_backoff, backoff * 2.0 + random.uniform(0, 1.0))
                        time.sleep(backoff)
                else:
                    # nothing to do, sleep small
                    time.sleep(0.6)
                    # reset backoff when manually disabled/connected
                    if getattr(self.rpc, "_connected", False):
                        backoff = self.base_delay
            except Exception as e:
                self._enqueue_ui(self._append_log, f"Reconnect manager exception: {e}", 'ERROR')
                time.sleep(1.0)

    # Simulation fallback
    def _simulate_if_disconnected(self):
        try:
            if not self.rpc._connected:
                if HAS_PSUTIL:
                    cpu = psutil.cpu_percent(interval=None)
                    mem = psutil.virtual_memory().percent
                else:
                    cpu = (math.sin(time.time()/3.0) * 20.0) + 30.0
                    mem = 40.0 + (math.cos(time.time()/6.0) * 10.0)
                uptime = f"{int(time.time()//60):02d}m"
                payload = {"cpu": round(float(cpu), 1), "ram": round(float(mem), 1), "uptime": uptime}
                self._handle_event('sysinfo', payload)
        except Exception as e:
            self._append_log(f"Simulate error: {e}", 'ERROR')
        finally:
            self.after(1200, self._simulate_if_disconnected)

# Run
if __name__ == '__main__':
    app = PanelApp()
    app.after(100, app._process_ui_queue)
    app.mainloop()
