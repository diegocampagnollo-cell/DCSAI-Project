# rpc_panel_gui_plotly.py
# DCs.AI Cyber Panel+ (Fase 116.6)
# Radar Interativo (Plotly) embutido no painel CustomTkinter
# Requisitos: customtkinter, plotly, pillow (PIL). Kaleido recommended but optional (fallback to matplotlib).

"""
Execução: python rpc_panel_gui_plotly.py

Descrição:
- Painel GUI com backend RPCClient (compatível com seu rpc_panel gui atual).
- Radar Plotly embutido que atualiza com dados recebidos do core.
- Tenta usar plotly + kaleido para renderizar imagens PNG; se não disponível, cai para matplotlib.
- O radar mostra métricas: CPU, RAM, Uptime (normalizado), Peers, Latency.

Observações:
- Se tiver problemas com dependências, instale:
  pip install customtkinter plotly pillow kaleido

"""

import os
import time
import json
import asyncio
import threading
import queue
from datetime import datetime
from io import BytesIO

import customtkinter as ctk
from PIL import Image, ImageTk

# try plotly + kaleido (preferred)
USE_PLOTLY = True
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    # ensure kaleido is usable; to_image will raise if not
    pio.kaleido.scope.default_format = "png"
except Exception:
    USE_PLOTLY = False

# fallback to matplotlib radar
USE_MATPLOTLIB = False
if not USE_PLOTLY:
    try:
        import matplotlib.pyplot as plt # type: ignore
        import numpy as np # type: ignore
        USE_MATPLOTLIB = True
    except Exception:
        USE_MATPLOTLIB = False

# ------------------ Configs ------------------
DEFAULT_HOST = os.environ.get("DCS_RPC_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("DCS_RPC_PORT", "22888"))
AUTH_TOKEN = os.environ.get("DCS_RPC_TOKEN") or "panel_token"
os.environ["DCS_RPC_TOKEN"] = AUTH_TOKEN

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# small helper
def ts():
    return datetime.now().strftime("%H:%M:%S")

# ------------------ Radar renderer ------------------
class RadarRenderer:
    """Renderiza o radar como imagem (PNG) a partir de um dicionário de métricas."""
    def __init__(self, size=(480,480)):
        self.size = size

    def metrics_to_radar(self, metrics: dict):
        # normalize metrics into 0..1 (we'll map to 0..100 for percentage visuals)
        cpu = float(metrics.get('cpu', 0.0))
        ram = float(metrics.get('ram', 0.0))
        uptime = float(metrics.get('uptime_norm', metrics.get('uptime', 0.0)))
        peers = float(metrics.get('peers', 0.0))
        lat = float(metrics.get('latency', metrics.get('lat', 0.0)))
        # Map to 0..100
        vals = [cpu, ram, min(uptime*100,100), min(peers*10,100), min(lat,100)]
        labels = ['CPU', 'RAM', 'UPTIME', 'PEERS', 'LATENCY']
        return labels, vals

    def render_png(self, metrics: dict) -> bytes:
        labels, vals = self.metrics_to_radar(metrics)
        if USE_PLOTLY:
            try:
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=labels + [labels[0]], fill='toself', name='sys'))
                fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0,100])),
                                  paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=10),
                                  showlegend=False)
                # aesthetic neon style
                fig.update_traces(line=dict(color='cyan', width=3), fillcolor='rgba(0,255,200,0.15)')
                img_bytes = pio.to_image(fig, format='png', width=self.size[0], height=self.size[1])
                return img_bytes
            except Exception as e:
                print(f"[RadarRenderer] Plotly render failed, fallback: {e}")
                # fall through to matplotlib if available
        if USE_MATPLOTLIB:
            try:
                # radar with matplotlib
                N = len(vals)
                angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
                vals2 = vals + vals[:1]
                angles2 = angles + angles[:1]
                fig = plt.figure(figsize=(self.size[0]/100, self.size[1]/100), dpi=100)
                ax = fig.add_subplot(111, polar=True)
                ax.plot(angles2, vals2, color='#00ffe0', linewidth=2)
                ax.fill(angles2, vals2, color='#00ffe033')
                ax.set_xticks(angles)
                ax.set_xticklabels(labels)
                ax.set_yticklabels([])
                fig.tight_layout(pad=0)
                buf = BytesIO()
                fig.savefig(buf, format='png', transparent=True)
                plt.close(fig)
                return buf.getvalue()
            except Exception as e:
                print(f"[RadarRenderer] Matplotlib render failed: {e}")
        # last resort: generate simple placeholder PNG via PIL
        return self._placeholder_png(metrics)

    def _placeholder_png(self, metrics: dict) -> bytes:
        from PIL import ImageDraw, ImageFont
        w,h = self.size
        img = Image.new('RGBA', (w,h), (10,10,10,255))
        draw = ImageDraw.Draw(img)
        txt = f"CPU:{metrics.get('cpu',0):.1f}%\nRAM:{metrics.get('ram',0):.1f}%\nPeers:{int(metrics.get('peers',0))}"
        try:
            f = ImageFont.load_default()
            draw.text((10,10), txt, font=f, fill=(0,255,200))
        except Exception:
            draw.text((10,10), txt, fill=(0,255,200))
        buf = BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

# ------------------ Simple RPCClient (reuse from panel) ------------------
class RPCClientMini:
    """Very small async RPC client: connects, authenticates, and calls event_cb on messages."""
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, token=AUTH_TOKEN, log_cb=None, event_cb=None):
        self.host = host
        self.port = port
        self.token = token
        self.log_cb = log_cb or (lambda m, lvl='INFO': None)
        self.event_cb = event_cb or (lambda ev, d: None)
        self.reader = None
        self.writer = None
        self._connected = False
        self._loop = None
        self._task = None

    def log(self, message, level='INFO'):
        try:
            self.log_cb(f"[{ts()}] {message}", level)
        except Exception:
            pass

    async def connect(self):
        try:
            self.log(f"Connecting to {self.host}:{self.port}...", 'INFO')
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self._connected = True
            self.log('Connected', 'INFO')
            # auth
            token_msg = json.dumps({"type":"auth","token":self.token}) + '\n'
            self.writer.write(token_msg.encode())
            await self.writer.drain()
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
                    self.log('Connection closed by remote', 'WARN')
                    self._connected = False
                    self.event_cb('disconnected', None)
                    break
                try:
                    data = json.loads(line.decode().strip())
                except Exception:
                    data = line.decode(errors='ignore').strip()
                self.log(f"RX {data}", 'RX')
                self.event_cb('message', data)
        except asyncio.CancelledError:
            self.log('Reader loop cancelled', 'DEBUG')
        except Exception as e:
            self.log(f"Reader loop error: {e}", 'ERROR')
            self._connected = False
            self.event_cb('disconnected', None)

    async def _send(self, payload: dict):
        if not self._connected or not self.writer:
            raise ConnectionError('Not connected')
        text = json.dumps(payload, ensure_ascii=False) + '\n'
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

# ------------------ Panel App with Radar ------------------
class PanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('⚡ DCs.AI Cyber Panel+ (Radar)')
        self.geometry('1100x700')

        # loop + client
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()
        self.rpc = RPCClientMini(log_cb=self._log, event_cb=self._on_event)

        # radar renderer
        self.renderer = RadarRenderer(size=(440,440))
        self._latest_metrics = {'cpu':0.0,'ram':0.0,'uptime_norm':0.0,'peers':0,'latency':0}

        self._ui_q = queue.Queue()
        self._build_ui()
        self.after(100, self._process_ui_queue)
        self._render_lock = threading.Lock()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _build_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill='x', padx=12, pady=10)
        ctk.CTkLabel(top, text='DCs.AI Cyber Panel+ — Radar', font=('Consolas',22,'bold')).pack(side='left')

        ctrl = ctk.CTkFrame(self)
        ctrl.pack(fill='x', padx=12, pady=(0,10))
        self.host_entry = ctk.CTkEntry(ctrl, width=200)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.pack(side='left', padx=6)
        self.port_entry = ctk.CTkEntry(ctrl, width=100)
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.port_entry.pack(side='left', padx=6)
        ctk.CTkButton(ctrl, text='Conectar', command=self._on_connect).pack(side='left', padx=6)
        ctk.CTkButton(ctrl, text='Desconectar', command=self._on_disconnect).pack(side='left', padx=6)
        ctk.CTkButton(ctrl, text='Ping', fg_color='#0088FF', command=self._on_ping).pack(side='left', padx=6)

        main = ctk.CTkFrame(self)
        main.pack(fill='both', expand=True, padx=12, pady=(0,12))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)

        # left: logs
        self.logbox = ctk.CTkTextbox(main, width=580, height=520)
        self.logbox.grid(row=0, column=0, sticky='nsew', padx=(0,8))
        self.logbox.insert('end', '🟢 Painel iniciado — Radar ativo.\n')

        # right: radar + stats
        side = ctk.CTkFrame(main, width=440)
        side.grid(row=0, column=1, sticky='n', padx=(8,0))
        self.radar_label = ctk.CTkLabel(side, text='')
        self.radar_label.pack(pady=6)

        stats_frame = ctk.CTkFrame(side)
        stats_frame.pack(fill='x', padx=6, pady=(6,0))
        self.stats_text = ctk.CTkLabel(stats_frame, text='CPU: 0%\nRAM: 0%\nUptime: 0s\nPeers: 0\nLat: 0ms', anchor='w')
        self.stats_text.pack(fill='x', padx=6, pady=6)

        # toggle radar update
        self._radar_enabled = True
        self.btn_toggle = ctk.CTkButton(side, text='Desativar Radar' if self._radar_enabled else 'Ativar Radar', command=self._toggle_radar)
        self.btn_toggle.pack(pady=6)

    def _process_ui_queue(self):
        try:
            while True:
                fn, a, k = self._ui_q.get_nowait()
                fn(*a, **k)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_ui_queue)

    def _enqueue_ui(self, fn, *a, **k):
        self._ui_q.put((fn,a,k))

    def _log(self, message, level='INFO'):
        self._enqueue_ui(self._append_log, message, level)

    def _append_log(self, message, level='INFO'):
        prefix = {'INFO':'ℹ️','WARN':'⚠️','ERROR':'❌','RX':'◀️','TX':'▶️'}.get(level,'')
        self.logbox.insert('end', f"{prefix} {message}\n")
        self.logbox.see('end')

    def _on_event(self, ev, data):
        # expects data to be dicts broadcasted from core with sysinfo keys
        # we'll try to parse and update radar
        if isinstance(data, dict):
            # normalize possible structures
            if data.get('method') == 'status_update' and isinstance(data.get('params'), dict):
                m = data['params']
            else:
                m = data
            # populate sanitized metrics
            metrics = {
                'cpu': float(m.get('cpu', 0.0)),
                'ram': float(m.get('mem', m.get('ram', 0.0))),
                'uptime_norm': float(m.get('uptime_norm', (m.get('uptime',0)/60) if m.get('uptime') else 0.0)),
                'peers': int(m.get('peers', m.get('connections',0))),
                'latency': float(m.get('latency', m.get('lat',0)))
            }
            self._latest_metrics = metrics
            self._enqueue_ui(self._update_stats_display, metrics)
            if self._radar_enabled:
                # render radar image in background thread to avoid blocking
                threading.Thread(target=self._render_and_set_radar, args=(metrics,), daemon=True).start()
        else:
            self._append_log(f"Event: {data}", 'INFO')

    def _update_stats_display(self, metrics):
        txt = f"CPU: {metrics['cpu']:.1f}%\nRAM: {metrics['ram']:.1f}%\nUptime(norm): {metrics['uptime_norm']:.2f}\nPeers: {metrics['peers']}\nLat: {metrics['latency']:.1f}ms"
        self.stats_text.configure(text=txt)

    def _render_and_set_radar(self, metrics):
        with self._render_lock:
            try:
                png = self.renderer.render_png(metrics)
                img = Image.open(BytesIO(png)).convert('RGBA')
                ctk_img = ctk.CTkImage(light_image=img, size=self.renderer.size)
                # enqueue UI update
                self._enqueue_ui(self._set_radar_image, ctk_img)
            except Exception as e:
                self._append_log(f"Radar render error: {e}", 'ERROR')

    def _set_radar_image(self, ctk_img):
        try:
            self.radar_label.configure(image=ctk_img)
            self.radar_label.image = ctk_img
        except Exception as e:
            self._append_log(f"Set radar image error: {e}", 'ERROR')

    def _on_connect(self):
        host = self.host_entry.get().strip() or DEFAULT_HOST
        try:
            port = int(self.port_entry.get().strip())
        except Exception:
            port = DEFAULT_PORT
        self.rpc.host = host
        self.rpc.port = port
        self._set_status('Conectando...')
        try:
            self.rpc.start_in_loop(self.loop)
            self._set_status('Conectado')
        except Exception as e:
            self._append_log(f'Erro iniciando conexão: {e}', 'ERROR')
            self._set_status('Erro')

    def _on_disconnect(self):
        try:
            self.rpc.stop()
            self._set_status('Desconectado')
        except Exception as e:
            self._append_log(f'Desconectar erro: {e}', 'ERROR')

    def _on_ping(self):
        payload = {"type":"request","method":"ping","id":int(time.time())}
        try:
            self.rpc.send_async(payload)
        except Exception as e:
            self._append_log(f'Ping falhou: {e}', 'ERROR')

    def _toggle_radar(self):
        self._radar_enabled = not self._radar_enabled
        self.btn_toggle.configure(text='Desativar Radar' if self._radar_enabled else 'Ativar Radar')

    def _set_status(self, text):
        self._enqueue_ui(self._append_log, f"[STATUS] {text}", 'INFO')

# ------------------ Run ------------------
if __name__ == '__main__':
    app = PanelApp()
    app.mainloop()
